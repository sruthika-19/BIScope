import type {
  AlternativeResponse,
  AssistantMessage,
  DetailedRequirementsResponse,
  EvidenceUploadResponse,
  RequirementSummary,
  SearchResponse,
  StandardDetail,
  StandardExplanation,
  TerminologyAnalysis,
} from '../types'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    const payload = await response.text()
    throw new Error(`${response.status}: ${payload || 'Request failed'}`)
  }

  return response.json() as Promise<T>
}

async function apiPost<T>(path: string, body: BodyInit | Record<string, unknown>, options?: RequestInit): Promise<T> {
  const requestOptions: RequestInit = {
    method: 'POST',
    ...options,
  }

  if (typeof body === 'string' || body instanceof FormData || body instanceof URLSearchParams) {
    requestOptions.body = body
  } else {
    requestOptions.body = JSON.stringify(body)
    if (!requestOptions.headers) {
      requestOptions.headers = { 'Content-Type': 'application/json' }
    }
  }

  const response = await fetch(`${API_BASE}${path}`, requestOptions)

  if (!response.ok) {
    const payload = await response.text()
    throw new Error(`${response.status}: ${payload || 'Request failed'}`)
  }

  return response.json() as Promise<T>
}

export function analyzeTerminology(query: string): Promise<TerminologyAnalysis> {
  return apiPost<TerminologyAnalysis>('/api/v1/terminology/analyze', { query })
}

export function searchStandards(query: string): Promise<SearchResponse> {
  return apiGet<SearchResponse>(`/api/v1/search?query=${encodeURIComponent(query)}`)
}

export function fetchStandardDetail(standardId: number): Promise<StandardDetail> {
  return apiGet<StandardDetail>(`/api/v1/standards/${standardId}`)
}

export function fetchStandardExplanation(productId: string, standardId: number): Promise<StandardExplanation> {
  return apiGet<StandardExplanation>(`/api/v1/standards/${standardId}/explanation?product_id=${encodeURIComponent(productId)}`)
}

export function fetchStandardAlternatives(productId: string, standardId: number): Promise<AlternativeResponse> {
  return apiGet<AlternativeResponse>(`/api/v1/standards/${standardId}/alternatives?product_id=${encodeURIComponent(productId)}`)
}

export function fetchRequirements(): Promise<{ requirements: RequirementSummary[] }> {
  return apiGet<{ requirements: RequirementSummary[] }>('/api/v1/requirements')
}

export function fetchProductRequirements(productId: string): Promise<RequirementSummary> {
  return apiGet<RequirementSummary>(`/api/v1/requirements/${encodeURIComponent(productId)}`)
}

export function fetchDetailedRequirements(productId: string): Promise<DetailedRequirementsResponse> {
  return apiGet<DetailedRequirementsResponse>(`/api/v1/requirements/${encodeURIComponent(productId)}/detailed`)
}

export function uploadEvidence(productId: string, file: File): Promise<EvidenceUploadResponse> {
  const formData = new FormData()
  formData.set('product_id', productId)
  formData.set('file', file)

  return apiPost<EvidenceUploadResponse>('/api/v1/evidence/upload', formData)
}

export function chatWithAssistant(
  message: string,
  history: AssistantMessage[],
  signal?: AbortSignal,
): Promise<{
  reply: string
  terminology: Record<string, unknown>
  clarification: Record<string, unknown>
  data_status: string
  sources: string[]
}> {
  return apiPost(
    '/api/v1/chat',
    {
      message,
      conversation_history: history,
    },
    signal ? { signal } : undefined,
  )
}
