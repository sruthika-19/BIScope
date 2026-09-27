export type Clarification = {
  needed: boolean
  question?: string | null
  reason?: string | null
}

export type ProductMatch = {
  product_id: string
  normalized_term: string
  extracted_attributes: Record<string, string[]>
  missing_critical_attributes: string[]
  heuristic_confidence: number
}

export type TerminologyAnalysis = {
  status: string
  products: ProductMatch[]
  normalized_query: string
  clarification: Clarification
}

export type SearchResult = {
  product_id?: string | null
  product_name?: string | null
  normalized_term?: string | null
  standard_id?: number | null
  standard_number?: string | null
  title?: string | null
  edition_year?: string | null
  status?: string | null
  qco_info?: string | null
}

export type SearchResponse = {
  query: string
  results: SearchResult[]
}

export type StandardDetail = {
  id: number
  standard_number?: string | null
  title?: string | null
  scope?: string | null
  edition_year?: string | null
  revision?: string | null
  newer_edition?: string | null
  source?: string | null
  status?: string | null
  qco_info?: string | null
}

export type StandardExplanation = {
  product_id: string
  standard_id: number
  standard_number: string
  relationship: string
  matches: string[]
  mismatches: string[]
  unknown: string[]
  explanation: string
}

export type StandardAlternative = {
  standard_id: number
  standard_number: string
  title?: string | null
  relationship: string
  matches: string[]
  mismatches: string[]
  unknown: string[]
  explanation: string
}

export type AlternativeResponse = {
  product_id: string
  selected_standard_id: number
  alternatives: StandardAlternative[]
}

export type RequirementSummary = {
  product_id: string
  product_name: string
  candidate_is_number: string
  status: string
}

export type DetailedRequirementItem = {
  requirement_id: string
  standard_id: string
  product_id: string
  requirement_description: string
  clause_reference: string
  limit_or_condition: string
  unit?: string | null
  comparison_type: string
  required_evidence: string
  evidence_type: string
  official_source: string
  verification_status: string
  verification_notes: string
}

export type DetailedRequirementsResponse = {
  standard_id: number
  standard_number: string
  product_id: string
  product_name: string
  title: string
  edition_year: number
  requirements_status: string
  requirements: DetailedRequirementItem[]
}

export type EvidenceResult = {
  requirement_id: string
  requirement_description: string
  required_evidence: string
  evidence_type: string
  status: string
  evidence_status: string
  matched_terms: string[]
  missing_terms: string[]
  message: string
}

export type EvidenceUploadResponse = {
  product_id: string
  filename: string
  extracted_text_length: number
  results: EvidenceResult[]
}

export type AssistantMessage = {
  role: 'user' | 'assistant'
  content: string
}
