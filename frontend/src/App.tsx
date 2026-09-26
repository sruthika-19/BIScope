import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkBreaks from 'remark-breaks'
import remarkGfm from 'remark-gfm'
import {
  BrowserRouter,
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from 'react-router-dom'
import {
  ArrowRight,
  Bot,
  Check,
  CheckCircle2,
  ChevronRight,
  Copy,
  FileCheck2,
  FileSearch,
  Lightbulb,
  LoaderCircle,
  Mic,
  MicOff,
  MoonStar,
  Search,
  ShieldCheck,
  SunMedium,
  UploadCloud,
  X,
} from 'lucide-react'
import './App.css'
import {
  analyzeTerminology,
  chatWithAssistant,
  fetchDetailedRequirements,
  fetchProductRequirements,
  fetchStandardAlternatives,
  fetchStandardDetail,
  fetchStandardExplanation,
  searchStandards,
  uploadEvidence,
} from './lib/api'
import type {
  AssistantMessage,
  DetailedRequirementsResponse,
  EvidenceResult,
  SearchResult,
  StandardAlternative,
  StandardDetail,
  StandardExplanation,
  TerminologyAnalysis,
} from './types'

type ThemeMode = 'dark' | 'light'

type JourneyState = {
  lastQuery: string
  normalizedTerm: string
  analysis: TerminologyAnalysis | null
  productId: string | null
  productName: string | null
  selectedStandardId: number | null
  currentStep: string
  requirementsContext: string
  evidenceContext: string
  evidenceProductId: string | null
  requirements: DetailedRequirementsResponse | null
  standardDetail: StandardDetail | null
  explanation: StandardExplanation | null
  alternatives: StandardAlternative[]
  evidenceResults: EvidenceResult[]
  candidateStandards: SearchResult[]
}

const STORAGE_KEY = 'biscope-journey-v1'
const THEME_KEY = 'biscope-theme-v1'

type SpeechRecognitionAlternativeLike = { transcript: string }
type SpeechRecognitionResultLike = ArrayLike<SpeechRecognitionAlternativeLike>
type SpeechRecognitionEventLike = { results: ArrayLike<SpeechRecognitionResultLike> }
type SpeechRecognitionErrorLike = { error: string }
type SpeechRecognitionLike = {
  lang: string
  interimResults: boolean
  onresult: ((event: SpeechRecognitionEventLike) => void) | null
  onerror: ((event: SpeechRecognitionErrorLike) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}
type SpeechRecognitionConstructor = new () => SpeechRecognitionLike

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor
    webkitSpeechRecognition?: SpeechRecognitionConstructor
  }
}

const defaultJourney: JourneyState = {
  lastQuery: '',
  normalizedTerm: '',
  analysis: null,
  productId: null,
  productName: null,
  selectedStandardId: null,
  currentStep: 'Find',
  requirementsContext: '',
  evidenceContext: '',
  evidenceProductId: null,
  requirements: null,
  standardDetail: null,
  explanation: null,
  alternatives: [],
  evidenceResults: [],
  candidateStandards: [],
}

function isBIScopeGeneralQuestion(question: string): boolean {
  const normalized = question.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
  return [
    /\btell me about biscope\b/,
    /\bdescribe biscope\b/,
    /\bwhat is biscope\b/,
    /\bwhat can (?:biscope|you) do\b/,
    /\bwhat does biscope do\b/,
    /\bhow does biscope work\b/,
    /\bhow does biscope help\b/,
    /\bwhat are the features of biscope\b/,
    /\bwhat features does biscope have\b/,
    /\bwhat is bis\b/,
  ].some((pattern) => pattern.test(normalized))
}

function useSpeechInput(onTranscript: (transcript: string) => void) {
  const [listening, setListening] = useState(false)
  const [speechError, setSpeechError] = useState('')
  const [recognition, setRecognition] = useState<SpeechRecognitionLike | null>(null)

  useEffect(
    () => () => {
      recognition?.stop()
    },
    [recognition],
  )

  const toggleListening = () => {
    setSpeechError('')
    if (listening) {
      recognition?.stop()
      setListening(false)
      return
    }

    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition
    if (!Recognition) {
      setSpeechError('Voice input is not supported in this browser.')
      return
    }

    const nextRecognition = new Recognition()
    nextRecognition.lang = 'en-IN'
    nextRecognition.interimResults = false
    nextRecognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript
      if (transcript) onTranscript(transcript)
    }
    nextRecognition.onerror = (event) => {
      setSpeechError(
        event.error === 'not-allowed'
          ? 'Allow microphone access to use voice input.'
          : 'Voice input could not be completed.',
      )
      setListening(false)
    }
    nextRecognition.onend = () => setListening(false)

    setRecognition(nextRecognition)
    setListening(true)
    try {
      nextRecognition.start()
    } catch {
      setListening(false)
      setSpeechError('Voice input could not be started.')
    }
  }

  return { listening, speechError, toggleListening }
}

function hasCandidateProduct(analysis: TerminologyAnalysis | null): boolean {
  return Boolean(
    analysis &&
      ['supported', 'multiple_products', 'needs_clarification'].includes(analysis.status) &&
      analysis.products.some(
        (product) => product.product_id?.trim() && product.normalized_term?.trim(),
      ),
  )
}

function hasSupportedProductContext(
  analysis: TerminologyAnalysis | null,
  productId: string | null,
): boolean {
  return Boolean(
    analysis &&
      ['supported', 'multiple_products'].includes(analysis.status) &&
      analysis.clarification.needed !== true &&
      productId?.trim() &&
      analysis.products.some(
        (product) =>
          product.product_id === productId &&
          product.product_id.trim() &&
          product.normalized_term.trim(),
      ),
  )
}

function hasValidProductContext(journey: JourneyState): boolean {
  return hasSupportedProductContext(journey.analysis, journey.productId)
}

function readJourney(): JourneyState {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (!saved) return defaultJourney

  try {
    const parsed = JSON.parse(saved) as Partial<JourneyState>
    return {
      ...defaultJourney,
      ...parsed,
      evidenceProductId:
        parsed.evidenceProductId ??
        (parsed.evidenceContext && parsed.evidenceResults?.length ? parsed.productId ?? null : null),
    }
  } catch {
    return defaultJourney
  }
}

function App() {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const stored = localStorage.getItem(THEME_KEY) as ThemeMode | null
    return stored ?? 'dark'
  })
  const [journey, setJourney] = useState<JourneyState>(() => readJourney())

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem(THEME_KEY, theme)
  }, [theme])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(journey))
  }, [journey])

  const resetJourney = () => {
    window.dispatchEvent(new Event('biscope:assistant-clear'))
    setJourney({ ...defaultJourney, lastQuery: '' })
  }

  return (
    <BrowserRouter>
      <div className="app-shell">
        <Header theme={theme} setTheme={setTheme} resetJourney={resetJourney} />
        <main className="app-main">
          <Routes>
            <Route
              path="/"
              element={<HomePage journey={journey} setJourney={setJourney} />}
            />
            <Route
              path="/explore"
              element={<ExplorePage journey={journey} setJourney={setJourney} />}
            />
            <Route
              path="/check"
              element={
                hasValidProductContext(journey) ? (
                  <CheckPage journey={journey} setJourney={setJourney} />
                ) : (
                  <Navigate to="/explore" replace />
                )
              }
            />
            <Route
              path="/services"
              element={<ServicesPage journey={journey} />}
            />
          </Routes>
        </main>
        <AssistantDock journey={journey} setJourney={setJourney} />
      </div>
    </BrowserRouter>
  )
}

function Header({
  theme,
  setTheme,
  resetJourney,
}: {
  theme: ThemeMode
  setTheme: (value: ThemeMode) => void
  resetJourney: () => void
}) {
  const location = useLocation()
  const navigate = useNavigate()
  const checkActive = location.pathname === '/check'

  return (
    <header className="topbar">
      <div className="brand-wrap">
        <button className="brand" type="button" onClick={() => navigate('/')}>
          <img
            className="brand-logo"
            src={theme === 'dark' ? '/logo-dark.png' : '/logo-light.png'}
            alt=""
            aria-hidden="true"
          />
          <span>BIScope</span>
        </button>
      </div>

      <nav className="nav" aria-label="Primary navigation">
        {[
          ['/', 'Home'],
          ['/explore', 'Explore'],
          ['/check#requirements', 'Check Requirements'],
          ['/check#evidence', 'Review Evidence'],
          ['/services', 'Services'],
        ].map(([to, label]) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `nav-link ${isActive || (to === '/' && location.pathname === '/') || (to.startsWith('/check#') && checkActive) ? 'active' : ''}`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="header-actions">
        <button
          type="button"
          className="ghost-button"
          onClick={() => {
            resetJourney()
            navigate('/')
          }}
        >
          Start New Search
        </button>
        <button
          type="button"
          className="icon-button"
          aria-label="Toggle theme"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        >
          {theme === 'dark' ? <SunMedium size={18} /> : <MoonStar size={18} />}
        </button>
      </div>
    </header>
  )
}

function HomePage({
  journey,
  setJourney,
}: {
  journey: JourneyState
  setJourney: (value: JourneyState | ((previous: JourneyState) => JourneyState)) => void
}) {
  const [query, setQuery] = useState(journey.lastQuery || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [homeStandards, setHomeStandards] = useState<SearchResult[]>([])
  const searchRequestSequenceRef = useRef(0)
  const searchInFlightRef = useRef(false)
  const navigate = useNavigate()
  useEffect(
    () => () => {
      searchRequestSequenceRef.current += 1
    },
    [],
  )
  const { listening, speechError, toggleListening } = useSpeechInput((transcript) => {
    setQuery((previous) => `${previous} ${transcript}`.trim())
  })

  const submitSearch = async (nextQuery: string) => {
    const cleanQuery = nextQuery.trim()
    if (!cleanQuery) {
      setError('Enter a product description to search.')
      return
    }
    if (searchInFlightRef.current) return

    const requestId = ++searchRequestSequenceRef.current
    searchInFlightRef.current = true
    setLoading(true)
    setError('')

    try {
      const analysis = await analyzeTerminology(cleanQuery)
      if (requestId !== searchRequestSequenceRef.current) return
      setJourney(() => ({
        ...defaultJourney,
        lastQuery: cleanQuery,
        normalizedTerm: analysis.normalized_query,
        analysis,
        productId: analysis.products[0]?.product_id ?? null,
        productName: analysis.products[0]?.normalized_term ?? null,
        currentStep: analysis?.clarification?.needed ? 'Clarify' : 'Explore',
      }))
      setHomeStandards([])
      if (analysis.clarification.needed) {
        navigate('/explore')
      } else if (analysis.products.length) {
        try {
          const results = await Promise.all(
            analysis.products.map((product) => searchStandards(product.product_id)),
          )
          if (requestId !== searchRequestSequenceRef.current) return
          const standards = results.flatMap((response) => response.results)
          setHomeStandards(standards)
          setJourney((previous) => ({ ...previous, candidateStandards: standards }))
        } catch (err) {
          if (requestId !== searchRequestSequenceRef.current) return
          setError(err instanceof Error ? err.message : 'Unable to load candidate standards.')
        }
      }
    } catch (err) {
      if (requestId !== searchRequestSequenceRef.current) return
      setError(err instanceof Error ? err.message : 'Unable to analyze the product description.')
    } finally {
      if (requestId === searchRequestSequenceRef.current) {
        searchInFlightRef.current = false
        setLoading(false)
      }
    }
  }

  const validProducts = journey.analysis?.products.filter(
    (product) => product.product_id && product.normalized_term,
  ) ?? []
  const supportedResult =
    journey.analysis &&
    ['supported', 'multiple_products'].includes(journey.analysis.status) &&
    journey.analysis.clarification.needed !== true &&
    validProducts.length > 0
  const unsupportedResult =
    journey.analysis &&
    (!['supported', 'multiple_products', 'needs_clarification'].includes(journey.analysis.status) ||
      validProducts.length === 0)

  const startNewSearch = () => {
    searchRequestSequenceRef.current += 1
    searchInFlightRef.current = false
    setLoading(false)
    window.dispatchEvent(new Event('biscope:assistant-clear'))
    setQuery('')
    setHomeStandards([])
    setJourney({ ...defaultJourney, lastQuery: '' })
    navigate('/')
  }

  return (
    <div className="home-page">
      <section className="hero-section">
      <div className="hero-panel">
        <div className="hero-copy">
          <div className="eyebrow">BIScope <span className="eyebrow-dot" /> PRODUCT TO STANDARD</div>
          <h1>FROM PRODUCT TO <span>BIS ACTION.</span></h1>
        <p className="hero-subtitle">
          Describe your product and find potentially relevant BIS standards and next steps.
        </p>
        </div>

        <div className="search-box home-search">
          <Search size={18} />
          <input
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') void submitSearch(query)
            }}
            placeholder="Describe your product…"
            aria-label="Product description"
          />
          {query.length > 0 || supportedResult ? (
            <button
              type="button"
              className="search-clear-button"
              onClick={startNewSearch}
              aria-label="Clear search"
              title="Clear search"
            >
              <X aria-hidden="true" size={15} strokeWidth={1.8} />
            </button>
          ) : null}
          <button
            type="button"
            className={`voice-button ${listening ? 'listening' : ''}`}
            aria-label={listening ? 'Stop voice input' : 'Use voice input'}
            title={listening ? 'Stop listening' : 'Use voice input'}
            onClick={toggleListening}
          >
            {listening ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
          <button type="button" onClick={() => submitSearch(query)} disabled={loading}>
            {loading ? <><LoaderCircle className="spin" size={16} /> Finding…</> : 'Find standard'}
          </button>
        </div>
        {speechError ? <div className="microphone-note">{speechError}</div> : null}
        {listening ? <div className="microphone-note is-listening">Listening…</div> : null}
        <div className="search-examples">
          <span>Try</span>
          {['industrial safety helmet', 'packaged drinking water'].map((example) => (
            <button type="button" key={example} onClick={() => setQuery(example)}>{example}</button>
          ))}
        </div>

        {error ? <div className="error-box">{error}</div> : null}

        {supportedResult ? (
          <div className="home-results reveal">
            <div className="results-heading">
              <div>
                <span className="section-kicker">MATCHED PRODUCT{validProducts.length > 1 ? 'S' : ''}</span>
                <h2>{validProducts.map((product) => product.normalized_term).join(' · ')}</h2>
              </div>
              <span className="status-chip">Candidate match</span>
            </div>
            {homeStandards.length ? (
              <div className="home-standard-list">
                {homeStandards.slice(0, 3).map((standard) => (
                  <article className="home-standard-card" key={`${standard.product_id}-${standard.standard_id}`}>
                    <span className="section-kicker">POTENTIALLY RELEVANT STANDARD</span>
                    <div className="home-standard-main">
                      <div>
                        <strong>{standard.standard_number || 'Standard number not currently available'}</strong>
                        <p>{standard.title || 'Title not currently available'}</p>
                      </div>
                      <span className="status-chip">{standard.status || 'To be verified'}</span>
                    </div>
                    <div className="card-action-row">
                      <button
                        type="button"
                        className="text-action"
                        onClick={() => {
                          const product = validProducts.find((item) => item.product_id === standard.product_id)
                          setJourney((previous) => ({
                            ...previous,
                            productId: product?.product_id ?? previous.productId,
                            productName: product?.normalized_term ?? previous.productName,
                            selectedStandardId: standard.standard_id ?? null,
                            currentStep: 'Verify',
                          }))
                          navigate('/explore')
                        }}
                      >
                        View standard <ChevronRight size={15} />
                      </button>
                      <button type="button" className="text-action" onClick={() => {
                        const product = validProducts.find((item) => item.product_id === standard.product_id)
                        setJourney((previous) => ({
                          ...previous,
                          productId: product?.product_id ?? previous.productId,
                          productName: product?.normalized_term ?? previous.productName,
                          selectedStandardId: standard.standard_id ?? null,
                        }))
                        navigate('/check#requirements')
                      }}>
                        Check requirements <ChevronRight size={15} />
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="empty-state">No candidate standard mapping is currently available in the BIScope dataset.</p>
            )}
          </div>
        ) : null}

        {unsupportedResult ? (
          <div className="home-no-match reveal">
            <span className="section-kicker">NO SUPPORTED PRODUCT MATCH</span>
            <p>I couldn’t identify a supported BIS product or question from that input. Try describing a product, Indian Standard, requirement, certification/service, or BIS-related question.</p>
            <button type="button" className="text-action" onClick={startNewSearch}>Search again <ChevronRight size={15} /></button>
          </div>
        ) : null}
      </div>
      </section>

      <section className="landing-section">
        <div className="section-heading">
          <span className="section-kicker">A CLEARER ROUTE</span>
          <h2>What BIScope can help with</h2>
        </div>
        <div className="feature-grid">
          {[
            { number: '01', icon: FileSearch, title: 'Find Standards', description: 'Turn everyday product descriptions into potentially relevant BIS standards.', to: '/explore' },
            { number: '02', icon: ShieldCheck, title: 'Understand Requirements', description: 'Review available product requirements and what still needs verification.', to: '/check#requirements' },
            { number: '03', icon: FileCheck2, title: 'Review Evidence', description: 'Compare uploaded documents against available requirement categories.', to: '/check#evidence' },
            { number: '04', icon: Bot, title: 'Ask BIScope', description: 'Ask contextual questions about the product and its candidate standard.', to: '/explore' },
          ].map(({ number, icon: Icon, title, description, to }) => (
            <button
              type="button"
              className="feature-card"
              key={number}
              onClick={() => to === '/explore' && title === 'Ask BIScope'
                ? window.dispatchEvent(new Event('biscope:assistant-open'))
                : navigate(to)}
            >
              <div className="feature-card-top"><span>{number}</span><Icon size={19} /></div>
              <strong>{title}</strong>
              <p>{description}</p>
              <span className="feature-arrow"><ArrowRight size={16} /></span>
            </button>
          ))}
        </div>
      </section>

      <section className="landing-section process-section">
        <div className="section-heading">
          <span className="section-kicker">THE JOURNEY</span>
          <h2>From description to next step</h2>
        </div>
        <div className="process-track">
          {[
            { label: 'Product', complete: Boolean(journey.productId) },
            { label: 'Terminology', complete: Boolean(journey.analysis && !journey.analysis.clarification.needed) },
            { label: 'Standard', complete: Boolean(journey.selectedStandardId) },
            { label: 'Requirements', complete: journey.currentStep === 'Check' || journey.currentStep === 'Review' },
            { label: 'Evidence', complete: journey.currentStep === 'Review' },
            { label: 'BIS action', complete: false },
          ].map(({ label, complete }, index, steps) => (
            <div className={`process-step ${complete ? 'complete' : ''}`} key={label}>
              <span className="process-index">{complete ? <CheckCircle2 size={15} /> : `0${index + 1}`}</span>
              <span className="process-label">{label}</span>
              {index < steps.length - 1 ? <span className="process-connector" aria-hidden="true" /> : null}
            </div>
          ))}
        </div>
      </section>

      <section className="trust-section">
        <div className="trust-icon"><ShieldCheck size={21} /></div>
        <div>
          <span className="section-kicker">CLEAR ABOUT WHAT IS KNOWN</span>
          <h2>Source-backed by design</h2>
          <p>BIScope uses available dataset and API information, and marks details that need verification from official BIS sources.</p>
        </div>
      </section>
    </div>
  )
}

function ExplorePage({
  journey,
  setJourney,
}: {
  journey: JourneyState
  setJourney: (value: JourneyState | ((previous: JourneyState) => JourneyState)) => void
}) {
  const [query, setQuery] = useState(journey.lastQuery || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searchResultsProductId, setSearchResultsProductId] = useState<string | null>(null)
  const analyzeRequestSequenceRef = useRef(0)
  const analyzeInFlightRef = useRef(false)
  useEffect(
    () => () => {
      analyzeRequestSequenceRef.current += 1
    },
    [],
  )
  const [selectedProductId, setSelectedProductId] = useState<string | null>(
    journey.productId ?? journey.analysis?.products[0]?.product_id ?? null,
  )
  const [clarificationAnswer, setClarificationAnswer] = useState('')
  const navigate = useNavigate()
  const analysis = journey.analysis
  const productId = journey.productId
  const { listening, speechError, toggleListening } = useSpeechInput((transcript) => {
    if (analysis?.clarification.needed === true) {
      setClarificationAnswer((previous) => `${previous} ${transcript}`.trim())
    } else {
      setQuery((previous) => `${previous} ${transcript}`.trim())
    }
  })

  useEffect(() => {
    const product = analysis?.products.find(
      (candidate) => candidate.product_id === productId,
    )
    const canDiscoverStandards = hasSupportedProductContext(analysis, productId)

    if (!analysis || !canDiscoverStandards || !product?.product_id) return

    let cancelled = false

    const loadStandards = async () => {
      try {
        const response = await searchStandards(product.product_id)
        if (!cancelled) {
          setSearchResults(response.results || [])
          setSearchResultsProductId(product.product_id)
          setJourney((previous) => ({
            ...previous,
            candidateStandards: response.results || [],
            selectedStandardId:
              previous.selectedStandardId ?? response.results[0]?.standard_id ?? null,
          }))
        }
      } catch (err) {
        if (!cancelled) {
          setSearchResults([])
          setSearchResultsProductId(product.product_id)
          setJourney((previous) => ({
            ...previous,
            candidateStandards: [],
            selectedStandardId: null,
            standardDetail: null,
            explanation: null,
            alternatives: [],
          }))
          setError(err instanceof Error ? err.message : 'Unable to load candidate standards.')
        }
      }
    }

    void loadStandards()

    return () => {
      cancelled = true
    }
  }, [analysis, productId, setJourney])

  const handleAnalyze = async (nextQuery: string, isClarification = false) => {
    const answer = nextQuery.trim()
    const cleanQuery = isClarification
      ? [journey.lastQuery, answer].filter(Boolean).join(' ').trim()
      : answer
    if (!cleanQuery) {
      setError('Enter a product description to analyze.')
      return
    }
    if (analyzeInFlightRef.current) return

    const requestId = ++analyzeRequestSequenceRef.current
    analyzeInFlightRef.current = true
    setLoading(true)
    setError('')

    try {
      const analysis = await analyzeTerminology(cleanQuery)
      if (requestId !== analyzeRequestSequenceRef.current) return
      setSelectedProductId(analysis.products[0]?.product_id ?? null)
      setJourney(() => ({
        ...defaultJourney,
        lastQuery: cleanQuery,
        normalizedTerm: analysis.normalized_query,
        analysis,
        productId: analysis.products[0]?.product_id ?? null,
        productName: analysis.products[0]?.normalized_term ?? null,
        currentStep: analysis.clarification?.needed ? 'Clarify' : 'Explore',
      }))
      setQuery(cleanQuery)
      setClarificationAnswer('')
    } catch (err) {
      if (requestId !== analyzeRequestSequenceRef.current) return
      setError(err instanceof Error ? err.message : 'Unable to analyze this query.')
    } finally {
      if (requestId === analyzeRequestSequenceRef.current) {
        analyzeInFlightRef.current = false
        setLoading(false)
      }
    }
  }

  const clearSearch = () => {
    analyzeRequestSequenceRef.current += 1
    analyzeInFlightRef.current = false
    setLoading(false)
    window.dispatchEvent(new Event('biscope:assistant-clear'))
    setQuery('')
    setClarificationAnswer('')
    setError('')
    setSearchResults([])
    setSearchResultsProductId(null)
    setSelectedProductId(null)
    setJourney({ ...defaultJourney, lastQuery: '' })
  }

  useEffect(() => {
    if (
      !hasSupportedProductContext(analysis, productId) ||
      !journey.selectedStandardId ||
      !productId
    ) {
      return
    }

    const selectedStandardId = journey.selectedStandardId
    const selectedProductId = productId

    const loadDetails = async () => {
      try {
        const [detail, explanation, alternatives, requirements] = await Promise.all([
          fetchStandardDetail(selectedStandardId),
          fetchStandardExplanation(selectedProductId, selectedStandardId),
          fetchStandardAlternatives(selectedProductId, selectedStandardId),
          fetchDetailedRequirements(selectedProductId),
        ])

        setJourney((previous) => ({
          ...previous,
          standardDetail: detail,
          explanation,
          alternatives: alternatives.alternatives ?? [],
          requirements:
            requirements.standard_id === selectedStandardId &&
            requirements.product_id === selectedProductId
              ? requirements
              : previous.requirements,
        }))
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load standard context.')
      }
    }

    void loadDetails()
  }, [analysis, journey.selectedStandardId, productId, setJourney])

  const renderClarification = () => {
    if (
      !journey.analysis ||
      journey.analysis.clarification.needed !== true ||
      !hasCandidateProduct(journey.analysis)
    ) {
      return null
    }

    return (
      <section className="card">
        <div className="card-title-row">
          <Lightbulb size={18} />
          <h3>{journey.analysis.clarification.question}</h3>
        </div>
        <div className="inline-search clarification-control">
          <input
            type="text"
            value={clarificationAnswer}
            onChange={(event) => setClarificationAnswer(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') void handleAnalyze(clarificationAnswer, true)
            }}
            placeholder="Your answer"
            aria-label="Clarification answer"
          />
          <button
            type="button"
            className={`voice-button ${listening ? 'listening' : ''}`}
            aria-label={listening ? 'Stop voice input' : 'Use voice input'}
            onClick={toggleListening}
          >
            {listening ? <MicOff size={17} /> : <Mic size={17} />}
          </button>
          <button
            type="button"
            className="clarification-continue"
            onClick={() => handleAnalyze(clarificationAnswer, true)}
            disabled={loading || !clarificationAnswer.trim()}
          >
            {loading ? <><LoaderCircle className="spin" size={16} /> Checking…</> : 'Continue'}
          </button>
        </div>
        {speechError ? <div className="microphone-note">{speechError}</div> : null}
        {listening ? <div className="microphone-note is-listening">Listening…</div> : null}
        {error ? <div className="error-box">{error}</div> : null}
      </section>
    )
  }

  const needsClarification = journey.analysis?.clarification.needed === true
  const supportedProductContext = hasValidProductContext(journey)
  const hasAnalysis = journey.analysis !== null
  const hasNoMatch = hasAnalysis && !hasCandidateProduct(journey.analysis)
  const visibleSearchResults =
    supportedProductContext
      ? searchResultsProductId === journey.productId
        ? searchResults
        : journey.candidateStandards.filter((item) => item.product_id === journey.productId)
      : []
  const activeStandard =
    visibleSearchResults.find((item) => item.standard_id === journey.selectedStandardId) ??
    visibleSearchResults[0]
  const activeProduct = journey.analysis?.products.find((item) => item.product_id === journey.productId)
  const selectedRequirements =
    journey.requirements?.product_id === journey.productId &&
    journey.requirements.standard_id === journey.selectedStandardId
      ? journey.requirements
      : null
  const selectedStandardNumber =
    selectedRequirements?.standard_number ||
    activeStandard?.standard_number ||
    'Standard mapping'
  const selectedEditionYear = selectedRequirements?.edition_year
    ? String(selectedRequirements.edition_year)
    : null
  const standardRecordEdition = journey.standardDetail?.edition_year || null
  const standardBaseNumber = journey.standardDetail?.standard_number?.replace(/:\d{4}$/, '')
  const earlierEdition =
    selectedEditionYear &&
    standardRecordEdition &&
    selectedEditionYear !== standardRecordEdition
      ? `${standardBaseNumber || journey.standardDetail?.standard_number || selectedStandardNumber}:${standardRecordEdition}`
      : null
  const applicabilityUnverified = /to be verified|needs review|not verified/i.test(
    journey.standardDetail?.status || activeStandard?.status || '',
  )
  const qcoInformation =
    journey.standardDetail?.qco_info || activeStandard?.qco_info || ''

  return (
    <div className="page-shell">
      <section className="page-intro">
        <span className="section-kicker">FIND · UNDERSTAND · VERIFY</span>
        <h1>Explore standards</h1>
        <p>Describe a product to discover potential standard matches from BIScope data.</p>
      </section>
      {!needsClarification && !hasNoMatch ? (
        <section className="search-panel card">
          <div className="card-title-row">
            <Search size={18} />
            <h3>Find the standard behind the product</h3>
          </div>
          <div className="inline-search">
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') void handleAnalyze(query)
              }}
              placeholder="Describe the product naturally"
            />
            {query.length > 0 || supportedProductContext ? (
              <button
                type="button"
                className="search-clear-button"
                onClick={clearSearch}
                aria-label="Clear search"
                title="Clear search"
              >
                <X aria-hidden="true" size={15} strokeWidth={1.8} />
              </button>
            ) : null}
            <button
              type="button"
              className={`voice-button ${listening ? 'listening' : ''}`}
              aria-label={listening ? 'Stop voice input' : 'Use voice input'}
              onClick={toggleListening}
            >
              {listening ? <MicOff size={17} /> : <Mic size={17} />}
            </button>
            <button type="button" onClick={() => handleAnalyze(query)} disabled={loading}>
              {loading ? <><LoaderCircle className="spin" size={16} /> Analyzing…</> : 'Analyze'}
            </button>
          </div>
          {speechError ? <div className="microphone-note">{speechError}</div> : null}
          {listening ? <div className="microphone-note is-listening">Listening…</div> : null}
          {error ? <div className="error-box">{error}</div> : null}
        </section>
      ) : null}

      {renderClarification()}

      {supportedProductContext ? (
        <section className="product-standard-workspace">
          <header className="workspace-header">
            <div className="workspace-header-copy">
              <span className="section-kicker">MATCHED PRODUCT</span>
              <h2>{journey.productName || 'Supported product'}</h2>
              <p>
                BIScope found a supported product match. Candidate standards and applicability details
                should be verified against official BIS sources.
              </p>
            </div>
          </header>
          {activeProduct && Object.entries(activeProduct.extracted_attributes).length ? (
            <dl className="product-attributes">
              {Object.entries(activeProduct.extracted_attributes).map(([key, values]) => (
                <div key={key}><dt>{key}</dt><dd>{values.join(', ')}</dd></div>
              ))}
            </dl>
          ) : null}

          {(journey.analysis?.products.length ?? 0) > 1 ? (
            <div className="product-switcher">
              <span className="detail-label">Matched products</span>
              {(journey.analysis?.products ?? []).map((product) => (
                <button
                  key={product.product_id}
                  type="button"
                  className={`product-option ${selectedProductId === product.product_id ? 'selected' : ''}`}
                  onClick={() => {
                    setSelectedProductId(product.product_id)
                    setJourney((previous) => ({
                      ...previous,
                      productId: product.product_id,
                      productName: product.normalized_term,
                      selectedStandardId: null,
                      requirementsContext: '',
                      evidenceContext: '',
                      evidenceProductId: null,
                      requirements: null,
                      evidenceResults: [],
                      standardDetail: null,
                      explanation: null,
                      alternatives: [],
                      candidateStandards: [],
                    }))
                  }}
                >
                  <div className="product-meta">
                    <span className="muted">{product.product_id}</span>
                    <strong>{product.normalized_term}</strong>
                  </div>
                </button>
              ))}
            </div>
          ) : null}

          <section className="workspace-standard">
            <div className="workspace-standard-heading">
              <div>
                <span className="section-kicker">CANDIDATE STANDARD</span>
                <h3>{selectedStandardNumber}</h3>
              </div>
              <span className="status-chip">
                {journey.standardDetail?.status || activeStandard?.status || 'To be verified'}
              </span>
            </div>
            {visibleSearchResults.length > 1 ? (
              <div className="standard-switcher" aria-label="Candidate standards">
                {visibleSearchResults.map((result) => (
                  <button
                    key={`${result.standard_id}-${result.product_id}`}
                    type="button"
                    className={result.standard_id === activeStandard?.standard_id ? 'selected' : ''}
                    onClick={() => setJourney((previous) => ({
                      ...previous,
                      selectedStandardId: result.standard_id ?? null,
                      standardDetail: null,
                      explanation: null,
                      alternatives: [],
                      currentStep: 'Verify',
                    }))}
                  >
                    <strong>{result.standard_number}</strong>
                    <span>{result.title}</span>
                  </button>
                ))}
              </div>
            ) : null}
            {activeStandard ? (
              <div className="workspace-standard-title">
                <h2>{journey.standardDetail?.title || activeStandard.title || 'Title not currently available'}</h2>
                <p>
                  {applicabilityUnverified
                    ? 'QCO / certification applicability: To be verified against the latest applicable BIS/QCO information.'
                    : qcoInformation || 'QCO information is not currently available in the BIScope dataset.'}
                </p>
              </div>
            ) : null}
            {visibleSearchResults.length ? null : (
              <div className="empty-state">
                No candidate standard mapping is currently available in the BIScope dataset.
              </div>
            )}
            {journey.standardDetail ? (
              <dl className="workspace-detail-list">
                <div><dt>Scope</dt><dd>{journey.standardDetail.scope || 'Not currently available'}</dd></div>
                <div>
                  <dt>Currently selected standard</dt>
                  <dd>{selectedStandardNumber}</dd>
                </div>
                <div>
                  <dt>Edition / version</dt>
                  <dd>
                    {selectedEditionYear
                      ? `${selectedEditionYear} (selected dataset version)`
                      : standardRecordEdition
                        ? `${standardRecordEdition} (standard record edition; selected version not confirmed)`
                        : journey.standardDetail.revision || 'Not currently available'}
                  </dd>
                </div>
                {earlierEdition ? (
                  <div><dt>Earlier edition in standard record</dt><dd>{earlierEdition}</dd></div>
                ) : null}
                {journey.standardDetail.newer_edition ? (
                  <div>
                    <dt>Newer edition note in standard record</dt>
                    <dd>{journey.standardDetail.newer_edition}</dd>
                  </div>
                ) : null}
                <div><dt>Status</dt><dd>{journey.standardDetail.status || activeStandard?.status || 'To be verified'}</dd></div>
                <div>
                  <dt>Official source</dt>
                  <dd>
                    {journey.standardDetail.source?.startsWith('http') ? (
                      <a href={journey.standardDetail.source} target="_blank" rel="noreferrer">Open source <ArrowRight size={14} /></a>
                    ) : journey.standardDetail.source || 'Not currently available'}
                  </dd>
                </div>
              </dl>
            ) : null}
          </section>

          {journey.explanation ? (
            <section className="workspace-why">
              <div className="workspace-section-heading">
                <Lightbulb size={17} />
                <h3>Why this standard</h3>
              </div>
              <p>{journey.explanation.explanation}</p>
              <div className="explanation-groups">
                {journey.explanation.matches.length ? (
                  <div><span className="detail-label">Matches</span><ul>{journey.explanation.matches.slice(0, 3).map((item) => <li key={item}>{item}</li>)}</ul></div>
                ) : null}
                {journey.explanation.mismatches.length ? (
                  <div><span className="detail-label">Mismatches</span><ul>{journey.explanation.mismatches.slice(0, 3).map((item) => <li key={item}>{item}</li>)}</ul></div>
                ) : null}
                {journey.explanation.unknown.length ? (
                  <div><span className="detail-label">Needs verification</span><ul>{journey.explanation.unknown.slice(0, 3).map((item) => <li key={item}>{item}</li>)}</ul></div>
                ) : null}
              </div>
            </section>
          ) : null}

          {journey.alternatives.length ? (
            <details className="workspace-alternatives">
              <summary>Alternative candidate standards <span>{journey.alternatives.length}</span></summary>
              <ul>
                {journey.alternatives.slice(0, 3).map((alternative) => (
                  <li key={alternative.standard_id}>
                    <strong>{alternative.standard_number} — {alternative.title}</strong>
                    <p>{alternative.explanation}</p>
                  </li>
                ))}
              </ul>
            </details>
          ) : null}

          <footer className="workspace-next">
            <div>
              <span className="detail-label">NEXT ACTION</span>
              <strong>Review available requirements and evidence</strong>
            </div>
            <button type="button" className="primary-link" onClick={() => navigate('/check#requirements')}>
              Continue to requirements <ArrowRight size={16} />
            </button>
          </footer>
        </section>
      ) : null}

      {hasNoMatch ? (
        <section className="card warning-card">
          <div className="card-title-row">
            <h3>No supported product match</h3>
          </div>
          <p className="unsupported-recovery-copy">I couldn’t identify a supported BIS product or question from that input. Try describing a product, Indian Standard, requirement, certification/service, or BIS-related question.</p>
          <button type="button" className="primary-link" onClick={() => navigate('/')}>
            Search again
          </button>
        </section>
      ) : null}

    </div>
  )
}

function CheckPage({
  journey,
  setJourney,
}: {
  journey: JourneyState
  setJourney: (value: JourneyState | ((previous: JourneyState) => JourneyState)) => void
}) {
  const location = useLocation()
  const [requirementsLoading, setRequirementsLoading] = useState(true)
  const [requirements, setRequirements] = useState<DetailedRequirementsResponse | null>(null)
  const [summary, setSummary] = useState<{ product_id: string; product_name: string; candidate_is_number: string; status: string } | null>(null)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadResult, setUploadResult] = useState<{
    product_id: string
    filename: string
    extracted_text_length: number
    results: EvidenceResult[]
  } | null>(null)

  useEffect(() => {
    if (!journey.productId) return

    const productId = journey.productId
    let cancelled = false
    const loadRequirements = async () => {
      const [detailResponse, summaryResponse] = await Promise.allSettled([
        fetchDetailedRequirements(productId),
        fetchProductRequirements(productId),
      ])

      if (cancelled) return
      setRequirementsLoading(false)

      if (detailResponse.status === 'fulfilled') {
        setRequirements(detailResponse.value)
      } else {
        setRequirements(null)
      }
      if (summaryResponse.status === 'fulfilled') {
        setSummary(summaryResponse.value)
      } else {
        setSummary(null)
      }

      const failures = [detailResponse, summaryResponse].filter(
        (result): result is PromiseRejectedResult => result.status === 'rejected',
      )
      const unexpectedFailure = failures.find((result) => !String(result.reason).startsWith('404:'))
      if (unexpectedFailure) {
        setError(`Unable to load requirements: ${unexpectedFailure.reason instanceof Error ? unexpectedFailure.reason.message : 'Please try again.'}`)
      } else {
        setError('')
      }
      setJourney((previous) => ({
        ...previous,
        requirements: detailResponse.status === 'fulfilled' ? detailResponse.value : null,
        requirementsContext:
          summaryResponse.status === 'fulfilled'
            ? `${summaryResponse.value.product_name} · ${summaryResponse.value.candidate_is_number} · ${summaryResponse.value.status}`
            : previous.productName ?? '',
        currentStep: 'Check',
      }))
    }

    void loadRequirements()

    return () => {
      cancelled = true
    }
  }, [journey.productId, setJourney])

  useEffect(() => {
    const target = document.getElementById(location.hash.slice(1))
    target?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [location.hash])

  const handleFile = async (file?: File) => {
    if (!file || !journey.productId) return

    setUploading(true)
    setError('')

    try {
      const result = await uploadEvidence(journey.productId, file)
      setUploadResult(result)
      setJourney((previous) => ({
        ...previous,
        evidenceContext: result.filename,
        evidenceProductId: result.product_id,
        evidenceResults: result.results,
        currentStep: 'Review',
      }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Evidence upload failed.')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const displayedEvidenceResults = uploadResult?.results ?? journey.evidenceResults
  const displayedEvidenceFile = uploadResult?.filename || journey.evidenceContext
  const requirementsStandard =
    requirements?.product_id === journey.productId
      ? formatRequirementStandard(requirements)
      : journey.standardDetail?.standard_number ||
        journey.candidateStandards.find((item) => item.standard_id === journey.selectedStandardId)?.standard_number ||
        'Candidate standard'

  return (
    <div className="page-shell">
      <section className="page-intro">
        <span className="section-kicker">VERIFY · REVIEW</span>
        <h1>Requirements & evidence</h1>
        <p>Review available requirements, then map a document against them.</p>
        <div className="review-context">
          <strong>{journey.productName || 'Current product'}</strong>
          <span>{requirementsStandard}</span>
          <span className="status-chip">{journey.standardDetail?.status || journey.candidateStandards.find((item) => item.standard_id === journey.selectedStandardId)?.status || 'To be verified'}</span>
        </div>
      </section>
      <div className="review-workspace">
      <section className="card" id="requirements">
        <div className="card-title-row">
          <ShieldCheck size={18} />
          <h3>Requirements</h3>
        </div>
        {summary ? (
          <div className="requirement-box">
            <strong>{summary.product_name}</strong>
            <span className="detail-label">Standard context</span>
            <p>
              {requirements?.product_id === journey.productId
                ? formatRequirementStandard(requirements)
                : summary.candidate_is_number}
            </p>
            <span className="status-chip">{summary.status}</span>
          </div>
        ) : requirementsLoading ? (
          <div className="loading-note"><LoaderCircle className="spin" size={16} /> Loading requirements…</div>
        ) : (
          <p>Detailed requirements are not currently available for this product.</p>
        )}

        {requirementsLoading ? null : requirements && requirements.requirements.length ? (
          <div className="requirements-list">
            {requirements.requirements.map((item) => (
              <div key={item.requirement_id} className="requirement-item">
                <details className="requirement-disclosure">
                  <summary>
                    <span className="requirement-summary-title">
                      <span className="requirement-id">{item.requirement_id}</span>
                      <strong>{item.requirement_description}</strong>
                    </span>
                    <span className={`status-chip ${item.verification_status.toLowerCase().replace(/\s+/g, '-')}`}>
                      {item.verification_status}
                    </span>
                  </summary>
                  <div className="requirement-content">
                    {item.limit_or_condition &&
                    !isRepeatedStandardContext(item.limit_or_condition, requirements.standard_number) ? (
                      <p>{item.limit_or_condition}</p>
                    ) : null}
                    <div className="requirement-detail-grid">
                      <div>
                        <span className="detail-label">Expected evidence</span>
                        <strong>{item.required_evidence}</strong>
                      </div>
                      <div>
                        <span className="detail-label">Clause</span>
                        <strong>{item.clause_reference}</strong>
                      </div>
                      <div>
                        <span className="detail-label">Verification</span>
                        <strong>{item.verification_status}</strong>
                        {item.verification_notes ? <p>{item.verification_notes}</p> : null}
                      </div>
                      <div>
                        <span className="detail-label">Source</span>
                        {item.official_source.startsWith('http') ? (
                          <a href={item.official_source} target="_blank" rel="noreferrer">{item.official_source}</a>
                        ) : (
                          <strong>{item.official_source || 'Not currently available'}</strong>
                        )}
                      </div>
                    </div>
                  </div>
                </details>
              </div>
            ))}
          </div>
        ) : !summary ? (
          <p>Requirements are not currently available for this product.</p>
        ) : (
          <p>Detailed requirements are not currently available for this product.</p>
        )}
        {error ? <div className="error-box">{error}</div> : null}
      </section>

      <section className="card" id="evidence">
        <div className="card-title-row">
          <UploadCloud size={18} />
          <h3>Evidence review</h3>
        </div>
        <div
          className={`upload-box ${dragOver ? 'drag-over' : ''} ${uploading ? 'uploading' : ''}`}
          onDragOver={(event) => {
            event.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(event) => {
            event.preventDefault()
            setDragOver(false)
            void handleFile(event.dataTransfer.files[0])
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt"
            onChange={(event) => void handleFile(event.target.files?.[0])}
          />
          <UploadCloud size={24} />
          <strong>{uploading ? 'Extracting and reviewing…' : 'Drop your document here'}</strong>
          <span>PDF or TXT · Scanned PDFs use OCR when available; handwriting recognition is not supported</span>
          <button type="button" className="browse-button" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            Browse files
          </button>
        </div>

        {error ? <div className="error-box">{error}</div> : null}

        {uploadResult || displayedEvidenceResults.length ? (
          <div className="evidence-results">
            <div className="label-row">
              <strong>{displayedEvidenceFile || 'Saved evidence mapping'}</strong>
              {uploadResult ? <span>{uploadResult.extracted_text_length} chars extracted</span> : null}
            </div>
            <div className="results-grid">
              {displayedEvidenceResults.map((result) => (
                <div key={result.requirement_id} className="evidence-item">
                  <div className="label-row">
                    <strong>{result.requirement_id}</strong>
                    <span className={`status-chip ${result.status.toLowerCase().replace(/\s+/g, '-')}`}>
                      {result.status}
                    </span>
                  </div>
                  <p>{result.requirement_description}</p>
                  <p className="evidence-message">{result.message}</p>
                  <div className="evidence-detail-grid">
                    <div>
                      <span className="detail-label">Required evidence</span>
                      <strong>{result.required_evidence}</strong>
                    </div>
                    <div>
                      <span className="detail-label">Matched</span>
                      <strong>{result.matched_terms.length ? result.matched_terms.join(', ') : 'None'}</strong>
                    </div>
                    <div>
                      <span className="detail-label">Missing</span>
                      <strong>{result.missing_terms.length ? result.missing_terms.join(', ') : 'None'}</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        <p className="disclaimer">
          Evidence review does not determine legal compliance or BIS certification.
        </p>
      </section>
      </div>
    </div>
  )
}

function isRepeatedStandardContext(condition: string, standardNumber: string): boolean {
  const normalize = (value: string) =>
    value.toLowerCase().replace(/:\d{4}/g, '').replace(/[.:]/g, '').replace(/\s+/g, ' ').trim()

  return normalize(condition) === normalize(`As specified in ${standardNumber}`)
}

type EvidenceCategory = 'Matched' | 'Partially matched' | 'Needs review' | 'Missing'

function getEvidenceCategory(result: EvidenceResult): EvidenceCategory {
  const status = `${result.status} ${result.evidence_status}`.toLowerCase()
  if (status.includes('partial')) return 'Partially matched'
  if (status.includes('review') || status.includes('uncertain')) return 'Needs review'
  if (status.includes('missing') || status.includes('not found') || result.missing_terms.length > 0) {
    if (result.matched_terms.length > 0 && result.missing_terms.length > 0) return 'Partially matched'
    return 'Missing'
  }
  if (result.matched_terms.length > 0 && result.missing_terms.length > 0) return 'Partially matched'
  if (status.includes('match') || result.matched_terms.length > 0) return 'Matched'
  return 'Needs review'
}

function formatRequirementForAssistant(item: DetailedRequirementsResponse['requirements'][number]): string {
  const details = [
    `**${item.requirement_id}: ${item.requirement_description}**`,
    item.clause_reference && `Clause: ${item.clause_reference}`,
    item.limit_or_condition && `Limit/condition: ${item.limit_or_condition}`,
    item.comparison_type && `Comparison: ${item.comparison_type}`,
    item.required_evidence && `Expected evidence: ${item.required_evidence}`,
    item.evidence_type && `Evidence type: ${item.evidence_type}`,
    `Verification status: ${item.verification_status || 'Not currently available'}`,
    item.verification_notes && `Note: ${item.verification_notes}`,
  ].filter(Boolean)
  const unextractedLimit =
    /^(as specified|not extracted|not available)/i.test(item.limit_or_condition.trim()) ||
    /exact (?:numerical )?limit is not extracted|limit.{0,30}not extracted/i.test(item.verification_notes)
  if (unextractedLimit) {
    details.push('The exact technical limit is not currently extracted in BIScope and should be checked in the official BIS source.')
  }
  if (/verified source available/i.test(item.verification_status)) {
    details.push('This status indicates source availability, not technical testing or compliance verification.')
  }
  return details.join('\n')
}

function markdownForAssistantDisplay(content: string): string {
  const boldDelimiters = [...content.matchAll(/\*\*/g)]
  if (boldDelimiters.length % 2 === 0) return content
  const unmatchedDelimiter = boldDelimiters[boldDelimiters.length - 1]
  const delimiterIndex = unmatchedDelimiter.index
  return delimiterIndex === undefined
    ? content
    : `${content.slice(0, delimiterIndex)}${content.slice(delimiterIndex + 2)}`
}

function formatRequirementStandard(requirements: DetailedRequirementsResponse): string {
  return /:\d{4}/.test(requirements.standard_number)
    ? requirements.standard_number
    : `${requirements.standard_number}${requirements.edition_year ? `:${requirements.edition_year}` : ''}`
}

function ServicesPage({ journey }: { journey: JourneyState }) {
  const services = [
    {
      title: 'Product Certification',
      description: 'Review the next official BIS process for certification and product clearance.',
      link: 'https://www.bis.gov.in/product-certification/product-certification-process/?lang=en',
    },
    {
      title: 'BIS Standards',
      description: 'Open the official BIS standards resource for relevant IS references.',
      link: 'https://www.services.bis.gov.in/php/BIS_2.0/dgdashboard/Published_Standards',
    },
    {
      title: 'Testing / Laboratory Information',
      description: 'Review the BIS testing and lab pathway for product verification.',
      link: 'https://www.bis.gov.in/laboratorys/testing-facility-and-testing-charges/?lang=en',
    },
    {
      title: 'Hallmarking',
      description: 'Check whether the product category requires hallmarking or marking-related review.',
      link: 'https://www.bis.gov.in/hallmarking-overview/mandatory-hallmarking-order/?lang=en',
    },
    {
      title: 'Consumer Services',
      description: 'Review BIS consumer support and public information channels.',
      link: 'https://www.bis.gov.in/consumer-overview/consumer-protection/?lang=en',
    },
    {
      title: 'Official BIS Resources',
      description: 'Open the BIS source to confirm current process details and official guidance.',
      link: 'https://www.services.bis.gov.in/php/BIS_2.0/eBIS/',
    },
  ]

  return (
    <div className="page-shell">
      <section className="page-intro">
        <span className="section-kicker">OFFICIAL RESOURCES</span>
        <h1>Take the next official step</h1>
        <p>Verify the applicable BIS process before taking action.</p>
        <div className="journey-pill-row">
          {journey.productName ? <span className="status-pill">{journey.productName}</span> : null}
          {journey.standardDetail?.standard_number ? <span className="status-pill">{journey.standardDetail.standard_number}</span> : null}
        </div>
      </section>

      <section className="card-grid">
        {services.map((service) => (
          <a key={service.title} className="service-card" href={service.link} target="_blank" rel="noreferrer">
            <strong>{service.title}</strong>
            <p>{service.description}</p>
            <span>Open official BIS source</span>
          </a>
        ))}
      </section>
    </div>
  )
}

type AssistantAction = {
  label: string
  route?: string
  prompt?: string
  href?: string
}

type AssistantChatMessage = AssistantMessage & {
  actions?: AssistantAction[]
}

function AssistantDock({
  journey,
  setJourney,
}: {
  journey: JourneyState
  setJourney: (value: JourneyState | ((previous: JourneyState) => JourneyState)) => void
}) {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [requestError, setRequestError] = useState('')
  const [retryQuestion, setRetryQuestion] = useState('')
  const [messages, setMessages] = useState<AssistantChatMessage[]>([])
  const [copiedMessageIndex, setCopiedMessageIndex] = useState<number | null>(null)
  const [copyFailedMessageIndex, setCopyFailedMessageIndex] = useState<number | null>(null)
  const [panelClosing, setPanelClosing] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const selectedContextStandardId =
    journey.selectedStandardId ??
    (journey.requirements?.product_id === journey.productId ? journey.requirements.standard_id : null)
  const contextProductRef = useRef(journey.productId)
  const contextStandardRef = useRef(selectedContextStandardId)
  const currentContextKeyRef = useRef(`${journey.productId ?? ''}:${selectedContextStandardId ?? ''}`)
  const requestSequenceRef = useRef(0)
  const requestAbortControllerRef = useRef<AbortController | null>(null)
  const requestTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const messagesContainerRef = useRef<HTMLDivElement | null>(null)
  const messageContentRefs = useRef(new Map<number, HTMLDivElement>())
  const followMessagesRef = useRef(true)
  const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const copyFeedbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const { listening, speechError, toggleListening } = useSpeechInput((transcript) => {
    setInput((previous) => `${previous} ${transcript}`.trim())
  })

  useLayoutEffect(() => {
    const productChanged = contextProductRef.current !== journey.productId
    const standardChanged = Boolean(
      selectedContextStandardId &&
      contextStandardRef.current &&
      selectedContextStandardId !== contextStandardRef.current,
    )
    if (productChanged) {
      contextProductRef.current = journey.productId
      contextStandardRef.current = selectedContextStandardId
    } else if (selectedContextStandardId) {
      contextStandardRef.current = selectedContextStandardId
    }
    currentContextKeyRef.current =
      `${journey.productId ?? ''}:${contextStandardRef.current ?? ''}`
    if (!productChanged && !standardChanged) return
    requestSequenceRef.current += 1
    requestAbortControllerRef.current?.abort()
    requestAbortControllerRef.current = null
    if (requestTimeoutRef.current) clearTimeout(requestTimeoutRef.current)
    requestTimeoutRef.current = null
    setMessages([])
    setInput('')
    setLoading(false)
    setRequestError('')
    setRetryQuestion('')
    setCopiedMessageIndex(null)
    setCopyFailedMessageIndex(null)
  }, [journey.productId, selectedContextStandardId])

  useLayoutEffect(() => {
    if (open && messages.length && followMessagesRef.current) {
      const container = messagesContainerRef.current
      if (container) container.scrollTop = container.scrollHeight
    }
  }, [messages, open])

  useEffect(() => () => {
    if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
    if (copyFeedbackTimerRef.current) clearTimeout(copyFeedbackTimerRef.current)
    if (requestTimeoutRef.current) clearTimeout(requestTimeoutRef.current)
    requestSequenceRef.current += 1
    requestAbortControllerRef.current?.abort()
    requestAbortControllerRef.current = null
    requestTimeoutRef.current = null
  }, [])

  const openAssistant = () => {
    if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
    closeTimerRef.current = null
    setPanelClosing(false)
    setOpen(true)
    followMessagesRef.current = true
  }

  const closeAssistant = () => {
    setPanelClosing(true)
    if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
    closeTimerRef.current = setTimeout(() => {
      setOpen(false)
      setPanelClosing(false)
      closeTimerRef.current = null
    }, 170)
  }

  const clearConversation = () => {
    requestSequenceRef.current += 1
    requestAbortControllerRef.current?.abort()
    requestAbortControllerRef.current = null
    if (requestTimeoutRef.current) clearTimeout(requestTimeoutRef.current)
    requestTimeoutRef.current = null
    setMessages([])
    setInput('')
    setLoading(false)
    setRequestError('')
    setRetryQuestion('')
    setCopiedMessageIndex(null)
    setCopyFailedMessageIndex(null)
    followMessagesRef.current = true
  }

  useEffect(() => {
    const handleClear = () => clearConversation()
    window.addEventListener('biscope:assistant-open', openAssistant)
    window.addEventListener('biscope:assistant-clear', handleClear)
    return () => {
      window.removeEventListener('biscope:assistant-open', openAssistant)
      window.removeEventListener('biscope:assistant-clear', handleClear)
    }
  }, [])

  const copyAssistantMessage = async (index: number) => {
    const readableText = messageContentRefs.current.get(index)?.innerText
    if (!readableText) return
    try {
      await navigator.clipboard.writeText(readableText)
      setCopiedMessageIndex(index)
      setCopyFailedMessageIndex(null)
    } catch {
      setCopiedMessageIndex(null)
      setCopyFailedMessageIndex(index)
    }
    if (copyFeedbackTimerRef.current) clearTimeout(copyFeedbackTimerRef.current)
    copyFeedbackTimerRef.current = setTimeout(() => {
      setCopiedMessageIndex(null)
      setCopyFailedMessageIndex(null)
      copyFeedbackTimerRef.current = null
    }, 1600)
  }

  const selectedStandard =
    journey.candidateStandards.find((item) => item.standard_id === journey.selectedStandardId) ??
    journey.candidateStandards[0] ??
    null
  const selectedRequirements =
    journey.requirements?.product_id === journey.productId &&
    journey.requirements.standard_id === journey.selectedStandardId
      ? journey.requirements
      : null
  const standardNumber =
    selectedRequirements
      ? formatRequirementStandard(selectedRequirements)
      : journey.standardDetail?.standard_number ?? selectedStandard?.standard_number ?? ''
  const pageName =
    location.pathname === '/explore' ? 'Explore' :
      location.pathname === '/check' ? 'Requirements & evidence' :
        location.pathname === '/services' ? 'Services' : 'Home'
  const contextLabel = [
    pageName,
    journey.productName,
    standardNumber,
  ].filter(Boolean).join(' · ')
  const officialSource =
    journey.standardDetail?.source ||
    journey.requirements?.requirements.find((item) => item.official_source.startsWith('http'))?.official_source ||
    ''
  const officialSourceUrl =
    (journey.standardDetail?.source?.startsWith('http') ? journey.standardDetail.source : null) ||
    journey.requirements?.requirements.find((item) => item.official_source.startsWith('http'))?.official_source ||
    ''

  const sourceActions = (): AssistantAction[] =>
    officialSourceUrl
      ? [{ label: 'Open official source', href: officialSourceUrl }]
      : []

  const reviewActions: AssistantAction[] = [
    { label: 'View Standard', route: '/explore' },
    { label: 'Review Requirements', route: '/check#requirements' },
  ]
  const standardStatus =
    journey.standardDetail?.status ?? selectedStandard?.status ?? 'To be verified'
  const candidateNote = standardNumber
    ? `BIScope currently identifies ${standardNumber} as a candidate standard for ${journey.productName || 'this product'}. Its listed status is "${standardStatus}"; scope and current certification/QCO applicability still need confirmation from an official BIS source.`
    : `BIScope has not returned a candidate standard for ${journey.productName || 'this product'}.`
  const currentEvidenceResults =
    journey.evidenceProductId === journey.productId ? journey.evidenceResults : []

  const getRequirements = async (): Promise<DetailedRequirementsResponse | null> => {
    if (!journey.productId) return null
    if (journey.requirements?.product_id === journey.productId) return journey.requirements

    try {
      const requirements = await fetchDetailedRequirements(journey.productId)
      setJourney((previous) =>
        previous.productId === journey.productId ? { ...previous, requirements } : previous,
      )
      return requirements
    } catch (err) {
      if (err instanceof Error && err.message.startsWith('404:')) return null
      throw err
    }
  }

  const answerFromJourney = async (question: string): Promise<Omit<AssistantChatMessage, 'role'> | null> => {
    const normalized = question.toLowerCase()
    const productId = journey.productId
    const selectedStandardId = selectedStandard?.standard_id ?? null

    const words = normalized.match(/[a-z]+/g) ?? []
    if (
      words.length >= 5 &&
      words.filter((word) => !/[aeiouy]/i.test(word)).length >= Math.ceil(words.length * 0.6)
    ) {
      return {
        content: 'I couldn’t identify a supported BIS product or question from that input. Try describing a product, Indian Standard, requirement, certification/service, or BIS-related question.',
        actions: [{ label: 'Try a product search', route: '/explore' }],
      }
    }

    if (/(what\s+(?:should\s+i|do\s+i|can\s+i|i\s+should)\s+(?:do\s+)?(?:now|next)|what\s+do\s+i\s+need\s+to\s+do|what\s+should\s+i\s+do|what\s+can\s+i\s+do|what next|what is next|next\s+steps?)/.test(normalized)) {
      if (!hasValidProductContext(journey)) {
        return {
          content: 'Start with a product description in Explore so BIScope can check for a supported product match.',
          actions: [{ label: 'Explore products', route: '/explore' }],
        }
      }
      const requirements = await getRequirements()
      const requirementUnavailable = !requirements?.requirements.length
      const requirementsStandard = requirements ? formatRequirementStandard(requirements) : standardNumber
      const evidenceTypes = [...new Set(
        (requirements?.requirements ?? [])
          .map((item) => item.required_evidence.trim())
          .filter(Boolean),
      )]
      const evidenceState = currentEvidenceResults.length
        ? `Evidence mapping: ${evidenceSummary(currentEvidenceResults)}.`
        : 'No evidence mapping has been run for this product yet.'
      const sourceVerification = /verify|review|to be verified|not verified/i.test(
        `${standardStatus} ${journey.standardDetail?.qco_info ?? selectedStandard?.qco_info ?? ''}`,
      )
        ? 'Confirm current certification/QCO applicability from the official BIS source; BIScope marks it for verification.'
        : 'Confirm current certification/QCO applicability from the official BIS source.'
      return {
        content: [
          `For ${journey.productName || 'this product'}${productId ? ` (${productId})` : ''}:`,
          requirementsStandard
            ? `Candidate standard: ${requirementsStandard}${selectedStandard?.title ? ` — ${selectedStandard.title}` : ''}.`
            : 'BIScope has not returned a candidate standard yet.',
          requirementUnavailable
            ? `Detailed requirements are not currently available from the requirements endpoint for ${productId}; do not infer them from the standard match.`
            : `BIScope has ${requirements.requirements.length} detailed requirements available. Review the expected evidence${evidenceTypes.length ? `, including ${evidenceTypes.slice(0, 7).join(', ')}` : ''}.`,
          sourceVerification,
          evidenceState,
          'Upload supporting documents in Evidence Review, then review any matched, partial, needs-review, or missing evidence results.',
          'A product/standard match and evidence mapping are not a certification or compliance determination.',
        ].join('\n\n'),
        actions: [
          { label: 'View Standard', route: '/explore' },
          { label: 'Review Requirements', route: '/check#requirements' },
          { label: currentEvidenceResults.length ? 'Review Evidence results' : 'Upload Evidence', route: '/check#evidence' },
          ...sourceActions(),
        ],
      }
    }

    if (/(why\b.*\b(product|selected|standard|match)|\bwhy this\b|\bwhy did you select\b|\bwhy.*\bselect(?:ed|ion)?\b|\bwhy.*\bchosen\b)/.test(normalized)) {
      const product = journey.analysis?.products.find((item) => item.product_id === productId)
      const attributes = product
        ? Object.entries(product.extracted_attributes)
            .flatMap(([key, values]) => values.map((value) => `${key}: ${value}`))
            .slice(0, 3)
        : []
      let explanation = journey.explanation
      if (!explanation && productId && selectedStandardId) {
        explanation = await fetchStandardExplanation(productId, selectedStandardId)
        setJourney((previous) => ({ ...previous, explanation }))
      }
      const standardDetail = journey.standardDetail ??
        (selectedStandardId ? await fetchStandardDetail(selectedStandardId) : null)
      if (standardDetail && !journey.standardDetail) {
        setJourney((previous) => ({ ...previous, standardDetail }))
      }
      const requirements = productId ? await getRequirements() : null
      const requirementsStandard = requirements ? formatRequirementStandard(requirements) : standardNumber
      const matchReason = journey.analysis
        ? `Your description (“${journey.lastQuery || journey.analysis.normalized_query}”) matched BIScope's supported product terminology${attributes.length ? ` and recorded attributes (${attributes.join('; ')})` : ''}.`
        : 'BIScope has no saved terminology analysis to explain this product match.'
      const explanationText = explanation?.explanation
        ? `Standard explanation: ${explanation.explanation}`
        : selectedStandardId
          ? 'A more specific standard explanation is not currently available.'
          : 'No candidate standard is currently linked to this product.'
      const requirementsContext = requirements?.requirements.length
        ? `BIScope also has ${requirements.requirements.length} detailed requirements available for review.`
        : ''
      return {
        content: [
          `${journey.productName || product?.normalized_term || 'Product'}${productId ? ` (${productId})` : ''}.`,
          requirementsStandard
            ? `Candidate standard: ${requirementsStandard}${standardDetail?.title || selectedStandard?.title ? ` — ${standardDetail?.title || selectedStandard?.title}` : ''}.`
            : 'No candidate standard is currently available.',
          matchReason,
          explanationText,
          requirementsContext,
          'This is a product/standard match, not a certification or compliance determination.',
        ].filter(Boolean).join('\n\n'),
        actions: [
          { label: 'View Standard', route: '/explore' },
          { label: 'Review Requirements', route: '/check#requirements' },
          ...sourceActions(),
        ],
      }
    }

    if (/(requirement|requirements|what should i review|what do i need(?! to do)|what evidence do i need|what (?:doc|document)s? do i need|what does .* require|what .* requirements)/.test(normalized)) {
      if (!productId) {
        return { content: 'Search for a supported product to review requirements.' }
      }
      const requirements = await getRequirements()
      if (!requirements?.requirements.length) {
        return {
          content: `Detailed requirements are not currently available from the requirements endpoint for ${journey.productName || productId}.`,
          actions: [...reviewActions, ...sourceActions()],
        }
      }
      const evidenceOnlyQuestion =
        /what evidence do i need|what (?:doc|document)s? do i need|expected evidence/.test(normalized)
      if (evidenceOnlyQuestion) {
        return {
          content: [
            `For ${requirements.product_name} (${requirements.product_id}), BIScope lists expected evidence for ${requirements.requirements.length} requirements.`,
            requirements.requirements.map((item) =>
              `${item.requirement_description}: ${item.required_evidence || 'Not specified in BIScope'}`,
            ).join('\n'),
            'Check the official BIS source for technical limits and current applicability.',
          ].join('\n\n'),
          actions: [{ label: 'Review Requirements', route: '/check#requirements' }, ...sourceActions()],
        }
      }
      const allRequested = /(all|every|full list|list all|complete list)/.test(normalized)
      const shownRequirements = allRequested
        ? requirements.requirements
        : requirements.requirements.slice(0, 3)
      return {
        content: [
          `For ${requirements.product_name} (${requirements.product_id}), BIScope currently has ${requirements.requirements.length} detailed requirements available for review.`,
          `${formatRequirementStandard(requirements)}${requirements.title ? ` — ${requirements.title}` : ''}.`,
          shownRequirements.map(formatRequirementForAssistant).join('\n\n'),
          !allRequested && requirements.requirements.length > shownRequirements.length
            ? 'Open Requirements to review the full list.'
            : '',
          '“Verified Source Available” means a source is available; it does not mean the product or requirement was technically tested.',
        ].filter(Boolean).join('\n\n'),
        actions: [{ label: 'Review Requirements', route: '/check#requirements' }, ...sourceActions()],
      }
    }

    if (/(what is missing|what(?:'s| is) missing|what evidence is missing|what documents? (?:are )?missing|did my document match|what did my upload cover|evidence.*(?:missing|review|upload|match|cover)|missing.*(?:evidence|document)|document.*(?:match|cover|review)|upload.*cover)/.test(normalized)) {
      if (!currentEvidenceResults.length) {
        return {
          content: journey.evidenceContext && journey.evidenceProductId === productId
            ? `The upload “${journey.evidenceContext}” is recorded, but it has no saved evidence-mapping results for this product.`
            : 'No evidence mapping has been run for this product yet. Upload a PDF or TXT document in Evidence Review to compare it with available requirements.',
          actions: [{ label: 'Open Evidence Review', route: '/check#evidence' }],
        }
      }
      const categories: EvidenceCategory[] = ['Matched', 'Partially matched', 'Needs review', 'Missing']
      const counts = categories.map((category) =>
        `${category}: ${currentEvidenceResults.filter((item) => getEvidenceCategory(item) === category).length}`,
      )
      const missingItems = currentEvidenceResults
        .filter((item) => getEvidenceCategory(item) === 'Missing' || item.missing_terms.length > 0)
        .slice(0, 3)
        .map((item) => `${item.requirement_id} (${getEvidenceCategory(item)}): ${item.missing_terms.length ? item.missing_terms.join(', ') : item.message}`)
      const details = currentEvidenceResults
        .slice(0, 3)
        .map((item) => `${item.requirement_id}: ${getEvidenceCategory(item)}${item.matched_terms.length ? `; detected ${item.matched_terms.join(', ')}` : ''}${item.missing_terms.length ? `; missing ${item.missing_terms.join(', ')}` : ''}.`)
      return {
        content: [
          `Evidence review for ${journey.productName || productId}:`,
          counts.join(' · '),
          missingItems.length ? `Terms flagged as missing by the mapper:\n${missingItems.join('\n')}` : details.join('\n'),
          'These results show document-to-requirement matching only. They do not determine BIS compliance or certification.',
        ].join('\n\n'),
        actions: [{ label: 'Review Evidence', route: '/check#evidence' }, { label: 'Review Requirements', route: '/check#requirements' }],
      }
    }

    if (/(certif|qco|compli|legal|mandatory|applicab|is it required|do i need.{0,30}(?:bis|licen[cs]e|mark|qco))/.test(normalized) &&
      !/(why|reason|explain)/.test(normalized)) {
      const qcoInfo = journey.standardDetail?.qco_info || selectedStandard?.qco_info
      return {
        content: [
          candidateNote,
          qcoInfo ? `BIScope listing: ${qcoInfo}` : 'QCO information is not currently available in the BIScope data.',
          'This is not a compliance or certification determination.',
        ].join('\n\n'),
        actions: sourceActions(),
      }
    }

    if (/(why|reason|suggest|recommend).*(standard|match|applicab)|(standard|match).*(suggest|recommend|why|reason|applicab)/.test(normalized)) {
      if (!productId || !selectedStandardId) {
        return { content: 'No selected candidate standard is available to explain yet.' }
      }
      const explanation = journey.explanation ??
        await fetchStandardExplanation(productId, selectedStandardId)
      if (!journey.explanation) {
        setJourney((previous) => ({ ...previous, explanation }))
      }
      const signals = [
        ...explanation.matches.slice(0, 2).map((item) => `Match: ${item}`),
        ...explanation.mismatches.slice(0, 2).map((item) => `Mismatch: ${item}`),
        ...explanation.unknown.slice(0, 2).map((item) => `Needs verification: ${item}`),
      ]
      return {
        content: `${explanation.explanation}${!explanation.explanation.toLowerCase().includes(standardStatus.toLowerCase()) ? `\n\nListed status: ${standardStatus}.` : ''}${signals.length ? `\n\n${signals.join('\n')}` : ''}`,
        actions: [
          { label: 'View Standard', route: '/explore' },
          { label: 'Review Requirements', route: '/check#requirements' },
        ],
      }
    }

    if (/(alternative|alternatives|different standard|other standard|another standard|why not)/.test(normalized)) {
      if (!productId || !selectedStandardId) {
        return { content: 'Select a candidate standard first to review alternatives.' }
      }
      const alternatives = journey.alternatives.length
        ? journey.alternatives
        : (await fetchStandardAlternatives(productId, selectedStandardId)).alternatives
      if (!journey.alternatives.length) {
        setJourney((previous) => ({ ...previous, alternatives }))
      }
      if (!alternatives.length) {
        return { content: 'No alternative candidate standards are currently available in the BIScope data.' }
      }
      return {
        content: `Other candidate standards in BIScope:\n${alternatives.slice(0, 3).map((item) => `${item.standard_number} — ${item.title}: ${item.explanation}`).join('\n')}`,
        actions: [{ label: 'View Standard options', route: '/explore' }],
      }
    }

    if (/(official source|source link|where.*source|source of|official bis)/.test(normalized)) {
      if (officialSource) {
        return {
          content: `BIScope's available source for ${standardNumber || 'this standard'}: ${officialSource}`,
          actions: sourceActions(),
        }
      }
      return { content: 'An official source link is not currently available in the loaded BIScope data. Verify the standard directly with BIS.' }
    }

    if (selectedStandardId && (/\b(detail|scope|edition|version|revision|standard number|standard title)\b|what.*cover|covers/.test(normalized))) {
      let detail = journey.standardDetail
      if (!detail) {
        try {
          detail = await fetchStandardDetail(selectedStandardId)
          setJourney((previous) => ({ ...previous, standardDetail: detail }))
        } catch (err) {
          if (err instanceof Error && err.message.startsWith('404:')) {
            return { content: 'Standard details are not currently available in BIScope for this candidate.' }
          }
          throw err
        }
      }
      const currentRequirements =
        journey.requirements?.product_id === productId &&
        journey.requirements.standard_id === selectedStandardId
          ? journey.requirements
          : null
      const currentStandardNumber = currentRequirements
        ? formatRequirementStandard(currentRequirements)
        : detail.standard_number
      const details = [
        currentStandardNumber && `Currently selected standard: ${currentStandardNumber}`,
        (currentRequirements?.title || detail.title) &&
          `Title: ${currentRequirements?.title || detail.title}`,
        detail.scope && `Scope: ${detail.scope}`,
        currentRequirements?.edition_year
          ? `Edition / version: ${currentRequirements.edition_year} (selected dataset version)`
          : detail.edition_year || detail.revision
            ? `Edition / version: ${detail.edition_year || detail.revision}`
            : '',
        currentRequirements?.edition_year &&
        detail.edition_year &&
        String(currentRequirements.edition_year) !== String(detail.edition_year)
          ? `Earlier edition in standard record: ${detail.standard_number}:${detail.edition_year}`
          : '',
        detail.newer_edition && `Newer edition note in standard record: ${detail.newer_edition}`,
        `Status: ${detail.status || standardStatus}`,
      ].filter(Boolean)
      return {
        content: `${details.join('\n') || 'Standard details are not currently available.'}\n\n${candidateNote}`,
        actions: sourceActions(),
      }
    }

    if (/(standard|candidate standard)/.test(normalized)) {
      return {
        content: `${candidateNote}${selectedStandard?.title ? `\n\n${selectedStandard.title}` : ''}`,
        actions: reviewActions,
      }
    }

    if (/(product|matched|identified|analy[sz]ed)/.test(normalized) && journey.analysis) {
      const match = journey.analysis.products.find((item) => item.product_id === productId)
      if (match) {
        const attributes = Object.entries(match.extracted_attributes)
          .slice(0, 3)
          .map(([key, values]) => `${key}: ${values.join(', ')}`)
        return {
          content: `BIScope matched ${match.normalized_term} (${match.product_id}) as a supported product.${attributes.length ? `\nAvailable details: ${attributes.join('; ')}.` : ''}\nA product match is not a certification or compliance determination.`,
          actions: reviewActions,
        }
      }
    }

    return null
  }

  const evidenceSummary = (results: EvidenceResult[]): string => {
    const categories: EvidenceCategory[] = ['Matched', 'Partially matched', 'Needs review', 'Missing']
    const counts = categories.map((category) =>
      `${category}: ${results.filter((item) => getEvidenceCategory(item) === category).length}`,
    )
    return counts.join(' · ')
  }

  const sendMessage = async (question = input, isRetry = false) => {
    const trimmed = question.trim()
    if (!trimmed) return
    if (requestAbortControllerRef.current) return

    const requestId = ++requestSequenceRef.current
    const requestContextKey = currentContextKeyRef.current
    const isApplicationQuestion = isBIScopeGeneralQuestion(trimmed)
    const previousMessages = messages
    const retryingLastQuestion = isRetry &&
      previousMessages.at(-1)?.role === 'user' &&
      previousMessages.at(-1)?.content === trimmed
    const historyMessages = retryingLastQuestion ? previousMessages.slice(0, -1) : previousMessages
    const history = historyMessages.slice(-8).map(({ role, content }) => ({ role, content }))
    const userMessage: AssistantMessage = { role: 'user', content: trimmed }
    const conversation: AssistantChatMessage[] = retryingLastQuestion
      ? previousMessages
      : [...previousMessages, userMessage]
    const controller = new AbortController()
    let timedOut = false
    let timeoutHandle: ReturnType<typeof setTimeout> | null = null
    const timeoutPromise = new Promise<never>((_resolve, reject) => {
      timeoutHandle = setTimeout(() => {
        timedOut = true
        controller.abort()
        const timeoutError = new Error('Assistant request timed out.')
        timeoutError.name = 'AssistantTimeoutError'
        reject(timeoutError)
      }, 25_000)
    })
    requestAbortControllerRef.current = controller
    requestTimeoutRef.current = timeoutHandle
    followMessagesRef.current = true
    setMessages(conversation)
    setInput('')
    setLoading(true)
    setRequestError('')
    setRetryQuestion('')

    try {
      const answerPromise = (async (): Promise<AssistantChatMessage> => {
        const groundedAnswer = isApplicationQuestion ? null : await answerFromJourney(trimmed)
        if (
          requestId !== requestSequenceRef.current ||
          requestContextKey !== currentContextKeyRef.current
        ) throw new Error('Assistant context changed during the request.')
        if (groundedAnswer) return { role: 'assistant', ...groundedAnswer }

        const requirements = journey.productId && !isApplicationQuestion
          ? await getRequirements()
          : null
        if (
          requestId !== requestSequenceRef.current ||
          requestContextKey !== currentContextKeyRef.current
        ) throw new Error('Assistant context changed during the request.')
        const currentRequirements =
          requirements?.product_id === journey.productId &&
          requirements.standard_id === journey.selectedStandardId
            ? requirements
            : null
        const currentStandardNumber = currentRequirements
          ? formatRequirementStandard(currentRequirements)
          : journey.standardDetail?.standard_number || selectedStandard?.standard_number || 'number unavailable'
        const currentStandardTitle =
          currentRequirements?.title ||
          journey.standardDetail?.title ||
          selectedStandard?.title ||
          'not available'
        const standardLifecycleContext =
          currentRequirements && journey.standardDetail?.edition_year &&
          String(journey.standardDetail.edition_year) !== String(currentRequirements.edition_year)
            ? `Standard record lifecycle: the standard-details endpoint lists edition ${journey.standardDetail.edition_year} and notes "${journey.standardDetail.newer_edition || 'no newer-edition note'}"; the currently selected detailed-requirements dataset version is ${currentStandardNumber}. Do not describe the standard-details edition as the currently selected version.`
            : ''
        const context = [
          journey.productId && `Product: ${journey.productName} (${journey.productId}); terminology status: ${journey.analysis?.status || 'not analyzed'}.`,
          selectedStandard && `Currently selected candidate standard: ${currentStandardNumber}; title: ${currentStandardTitle}; status: ${journey.standardDetail?.status || selectedStandard.status || 'To be verified'}; QCO listing: ${journey.standardDetail?.qco_info || selectedStandard.qco_info || 'not available'}.`,
          standardLifecycleContext,
          journey.standardDetail?.scope && `Scope: ${journey.standardDetail.scope}.`,
          journey.standardDetail?.source && `Standard source: ${journey.standardDetail.source}.`,
          journey.explanation && `Why this standard: ${journey.explanation.explanation}. Matches: ${journey.explanation.matches.join('; ')}. Mismatches: ${journey.explanation.mismatches.join('; ')}. Unknowns: ${journey.explanation.unknown.join('; ')}.`,
          journey.alternatives.length && `Alternatives: ${journey.alternatives.slice(0, 3).map((item) => `${item.standard_number} ${item.title}: ${item.explanation}`).join(' | ')}.`,
          currentRequirements?.requirements.length && `Detailed requirements: ${currentRequirements.requirements.length} records for ${currentRequirements.product_id} / ${currentStandardNumber}. ${currentRequirements.requirements.map((item) => `${item.requirement_id} ${item.requirement_description}; evidence ${item.required_evidence}; verification ${item.verification_status}`).join(' | ')}.`,
          journey.evidenceResults.length && `Evidence mapping: ${journey.evidenceResults.slice(0, 5).map((item) => `${item.requirement_id} status ${item.status}; matched ${item.matched_terms.join(', ') || 'none'}; missing ${item.missing_terms.join(', ') || 'none'}`).join(' | ')}.`,
        ].filter(Boolean).join('\n')
        const safeInstructions = isApplicationQuestion
          ? `User question: ${trimmed}`
          : [
              'Answer concisely using the BIScope context below before relying on general information.',
              'Do not invent standards, requirements, QCO applicability, certification status, technical limits, evidence, or test results.',
              'Never conclude that a product is compliant/certified or that certification is not required unless that exact verified conclusion is present in the supplied data.',
              'Preserve terms such as "candidate" and "To be verified". State when information is unavailable and recommend checking the official BIS source for current applicability.',
              'When the detailed-requirements data identifies the currently selected standard version, use that version as current. Keep any different standard-details edition separate as lifecycle information, not as the selected version.',
              'When relevant, repeat requirement IDs exactly as supplied in the detailed-requirements context. Do not invent or renumber requirement IDs.',
              `User question: ${trimmed}`,
              `BIScope context:\n${context || 'No product or standard context is currently available.'}`,
            ].join('\n\n')
        const response = await chatWithAssistant(safeInstructions, history, controller.signal)
        const unsafeClaim = /\b(?:is|are|has been|was)\s+(?:bis\s+)?(?:certified|compliant|in compliance)\b|\bno\s+(?:bis\s+)?certification\s+is\s+required\b|\b(?:does not|doesn't|do not|don't)\s+(?:require|need)\s+(?:a\s+)?(?:bis\s+)?certification\b|\b(?:satisfies|meets)\s+(?:all\s+)?(?:bis|the)\s+(?:requirements|standards)\b|\b(?:not required|not mandatory|not applicable|exempt from|not subject to)\b.{0,80}\b(?:bis|certification|standard|qco)\b|\b(?:bis|certification|standard|qco)\b.{0,80}\b(?:not required|not mandatory|not applicable|exempt|not subject to)\b/i
        const reply = unsafeClaim.test(response.reply)
          ? `I cannot establish a compliance or certification conclusion from the available BIScope data. ${candidateNote} Please confirm current applicability with the official BIS source.`
          : response.reply
        return {
          role: 'assistant',
          content: reply,
          actions: isApplicationQuestion ? [] : sourceActions(),
        }
      })()

      const assistantMessage = await Promise.race([answerPromise, timeoutPromise])
      if (
        requestId !== requestSequenceRef.current ||
        requestContextKey !== currentContextKeyRef.current
      ) return
      setMessages([...conversation, assistantMessage])
    } catch (err) {
      if (
        requestId !== requestSequenceRef.current ||
        requestContextKey !== currentContextKeyRef.current
      ) return
      const message = err instanceof Error ? err.message : ''
      const statusCode = message.match(/^(\d{3}):/)
      const errorMessage = timedOut
        ? 'Unable to get a response right now. The BIScope service is taking too long to respond.'
        : statusCode
          ? `The BIScope service returned an error (HTTP ${statusCode[1]}). Please try again.`
          : controller.signal.aborted
            ? 'The Assistant request was interrupted. Please try again.'
            : /failed to fetch|networkerror/i.test(message)
              ? 'Unable to reach the BIScope service. Check your connection and try again.'
              : 'Unable to get a response right now. Please try again.'
      setRequestError(errorMessage)
      setRetryQuestion(trimmed)
    } finally {
      if (timeoutHandle) clearTimeout(timeoutHandle)
      if (requestTimeoutRef.current === timeoutHandle) requestTimeoutRef.current = null
      if (requestAbortControllerRef.current === controller) requestAbortControllerRef.current = null
      if (
        requestId === requestSequenceRef.current &&
        requestContextKey === currentContextKeyRef.current
      ) setLoading(false)
    }
  }

  return (
    <div className={`assistant-dock ${open ? 'expanded' : ''} ${panelClosing ? 'closing' : ''}`}>
      {!open ? (
        <button type="button" className="assistant-toggle" onClick={openAssistant} aria-label="Open BIScope Assistant">
          <Bot size={18} />
          <span>BIScope Assistant</span>
        </button>
      ) : null}

      {open ? (
        <aside className="assistant-panel" role="dialog" aria-label="BIScope Assistant">
          <div className="assistant-header">
            <div className="assistant-title-group">
              <span className="assistant-mark"><Bot size={17} /></span>
              <div>
                <strong>BIScope Assistant</strong>
                <span>Ask about your BIScope journey.</span>
              </div>
            </div>
            <button type="button" className="assistant-close" onClick={closeAssistant} aria-label="Close BIScope Assistant">
              <X size={18} />
            </button>
          </div>
          <div className="assistant-context" title={contextLabel}>
            {contextLabel || 'No product context yet'}
          </div>

          <div
            className="assistant-messages"
            aria-live="polite"
            ref={messagesContainerRef}
            onScroll={(event) => {
              const element = event.currentTarget
              followMessagesRef.current =
                element.scrollHeight - element.clientHeight - element.scrollTop < 40
            }}
          >
            {!messages.length ? (
              <div className="assistant-empty">
                {journey.productName
                  ? `Ask about ${journey.productName}, its candidate standard, requirements, or evidence.`
                  : 'Analyze a product in BIScope to ask about its standards, requirements, or evidence.'}
              </div>
            ) : null}
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`message-group ${message.role}`}>
                <div className={`message ${message.role} ${message.role === 'assistant' ? 'message-markdown' : ''}`}>
                  {message.role === 'assistant' ? (
                    <>
                      <button
                        type="button"
                        className="message-copy-button"
                        aria-label={copiedMessageIndex === index ? 'Copied' : 'Copy assistant response'}
                        title={
                          copiedMessageIndex === index
                            ? 'Copied'
                            : copyFailedMessageIndex === index
                              ? 'Clipboard unavailable'
                              : 'Copy response'
                        }
                        onClick={() => void copyAssistantMessage(index)}
                      >
                        {copiedMessageIndex === index ? <Check size={14} /> : <Copy size={14} />}
                        {copiedMessageIndex === index ? <span>Copied</span> : null}
                      </button>
                      <div
                        className="message-content"
                        ref={(element) => {
                          if (element) messageContentRefs.current.set(index, element)
                          else messageContentRefs.current.delete(index)
                        }}
                      >
                        <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                          {markdownForAssistantDisplay(message.content)}
                        </ReactMarkdown>
                      </div>
                    </>
                  ) : (
                    <div className="message-content">{message.content}</div>
                  )}
                </div>
                {message.actions?.length ? (
                  <div className="assistant-message-actions">
                    {message.actions.map((action) => action.href ? (
                      <a key={action.label} href={action.href} target="_blank" rel="noreferrer">{action.label}</a>
                    ) : (
                      <button
                        key={action.label}
                        type="button"
                        onClick={() => {
                          if (action.route) {
                            closeAssistant()
                            navigate(action.route)
                          } else if (action.prompt) {
                            void sendMessage(action.prompt)
                          }
                        }}
                      >
                        {action.label}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
            {loading ? (
              <div className="message assistant generating-message" role="status">
                <span>Finding the relevant BIS information</span>
                <span className="typing-indicator" aria-hidden="true"><i /><i /><i /></span>
              </div>
            ) : null}
          </div>
          {requestError ? (
            <div className="assistant-error" role="alert">
              <span>{requestError}</span>
              {retryQuestion ? (
                <button
                  type="button"
                  className="assistant-retry-button"
                  onClick={() => void sendMessage(retryQuestion, true)}
                  disabled={loading}
                >
                  Retry
                </button>
              ) : null}
            </div>
          ) : null}
          {speechError ? <div className="microphone-note">{speechError}</div> : null}
          {listening ? <div className="microphone-note is-listening">Listening…</div> : null}

          <div className="assistant-input-row">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  void sendMessage()
                }
              }}
              rows={2}
              placeholder="Ask about this product or standard"
              aria-label="Message BIScope Assistant"
            />
            <div className="assistant-input-actions">
              <button
                type="button"
                className={`voice-button ${listening ? 'listening' : ''}`}
                onClick={toggleListening}
                aria-label={listening ? 'Stop voice input' : 'Use voice input'}
                title={listening ? 'Stop listening' : 'Use voice input'}
              >
                {listening ? <MicOff size={17} /> : <Mic size={17} />}
              </button>
              <button type="button" onClick={() => void sendMessage()} disabled={loading || !input.trim()}>
                {loading ? <LoaderCircle className="spin" size={16} /> : 'Send'}
              </button>
            </div>
          </div>
        </aside>
      ) : null}
    </div>
  )
}

export default App
