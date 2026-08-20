export type HealthResponse = {
  status: string
  service?: string
  version?: string
  readiness?: {
    configuration?: {
      gemini_configured?: boolean
      gemini_key_count?: number
      [key: string]: unknown
    }
    runtime?: {
      retrieval_mode?: string
      generation_mode?: string
      [key: string]: unknown
    }
    [key: string]: unknown
  }
}

export type LayerRow = {
  layer: string
  label?: string
  active: boolean
  clinical_topic?: string
  required_documents: string[]
  available_documents?: string[]
  description?: string
}

export type LayersResponse = {
  layers: LayerRow[]
}

export interface EvidenceChunk {
  chunk_id: string
  document_id?: string
  document_title?: string | null
  section_title?: string | null
  page_start?: number | null
  page_end?: number | null
  citation_label?: string | null
  chunk_type?: string | null
  disease_layer?: string | null
  similarity?: number
  content?: string
  rerank_score?: number
  lexical_overlap?: number
  expanded_lexical_overlap?: number
}

export interface LayerRoute {
  effective_layer?: string | null
  clinical_topic?: string | null
  allowed_document_ids?: string[]
  can_answer?: boolean
  route_status?: string
  reason?: string
}

export interface RetrievalConfidence {
  top_similarity?: number
  top_lexical_overlap?: number
  layer_match?: number
  evidence_count?: number
  composite_score?: number
  threshold?: number
  status?: string
  can_answer?: boolean
}

export interface AskRequest {
  question: string
  disease_layer?: string
  language?: string
  top_k?: number
  show_chunks?: boolean
}

export interface AskResponse {
  question: string
  layer?: LayerRoute
  safety?: {
    safety_label?: string
    reason?: string
    recommended_action?: string
  }
  confidence?: RetrievalConfidence
  retrieval?: {
    confidence?: string
    top_score?: number
    chunks?: EvidenceChunk[]
  }
  answer?: any
  substitutions?: any[]
  citation_validation?: any
  unsupported_claims?: any[]
}

export type EvidenceSearchRequest = {
  query: string
  disease_layer?: string
  clinical_topic?: string
  top_k?: number
}

export type EvidenceSearchResponse = {
  query: string
  layer?: LayerRoute
  disease_layer: string
  chunks: EvidenceChunk[]
}

export type FoodGuidanceItem = {
  food: string
  note: string
  evidence_chunk_id: string
  citation_label: string
}

export type FoodGuidanceListResponse = {
  disease_layer: string
  encouraged: FoodGuidanceItem[]
  suitable_with_caution: FoodGuidanceItem[]
  better_to_limit: FoodGuidanceItem[]
}

export type SubstitutionRequest = {
  food: string
  disease_layer?: string
  language?: string
}

export type SubstitutionItem = {
  instead_of: string
  alternative: string
  evidence_chunk_id: string
  citation_label: string
}

export type SubstitutionResponse = {
  food: string
  disease_layer: string
  alternatives: SubstitutionItem[]
}

export type EvaluationRunRequest = {
  limit?: number
  disease_layer?: string
}

export type EvaluationRunResponse = {
  metrics: {
    total_queries: number
    retrieval_precision_at_5: number
    citation_accuracy: number
    refusal_accuracy: number
    unsupported_claim_count: number
    average_retrieval_score: number
  }
  results: Array<Record<string, unknown>>
}

