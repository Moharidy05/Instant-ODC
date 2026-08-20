import type {
  AskRequest,
  AskResponse,
  EvaluationRunRequest,
  EvaluationRunResponse,
  EvidenceSearchRequest,
  EvidenceSearchResponse,
  FoodGuidanceListResponse,
  HealthResponse,
  LayersResponse,
  SubstitutionRequest,
  SubstitutionResponse,
} from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function requestJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${path}`
  let response: Response
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(options.headers ?? {}),
      },
    })
  } catch (error) {
    throw new ApiError(
      error instanceof Error ? `Backend offline or unreachable: ${error.message}` : 'Backend offline or unreachable',
    )
  }

  if (!response.ok) {
    const text = await response.text().catch(() => '')
    throw new ApiError(text || `Request failed with HTTP ${response.status}`, response.status)
  }

  return (await response.json()) as T
}

export function healthCheck() {
  return requestJson<HealthResponse>('/health')
}

export function getLayers() {
  return requestJson<LayersResponse>('/layers')
}

export function askFoodSafety(payload: AskRequest) {
  return requestJson<AskResponse>('/ask', {
    method: 'POST',
    body: JSON.stringify({
      question: payload.question,
      disease_layer: payload.disease_layer ?? 'auto',
      language: payload.language ?? 'en',
      top_k: payload.top_k ?? 5,
      show_chunks: payload.show_chunks ?? false,
    }),
  })
}

export function searchEvidence(payload: EvidenceSearchRequest) {
  return requestJson<EvidenceSearchResponse>('/evidence/search', {
    method: 'POST',
    body: JSON.stringify({
      query: payload.query,
      disease_layer: payload.disease_layer ?? 'auto',
      clinical_topic: payload.clinical_topic,
      top_k: payload.top_k ?? 5,
    }),
  })
}

export function getFoodGuidanceList(diseaseLayer = 'diabetes') {
  return requestJson<FoodGuidanceListResponse>(
    `/foods/guidance-list?disease_layer=${encodeURIComponent(diseaseLayer)}`,
  )
}

export function getSubstitutions(payload: SubstitutionRequest) {
  return requestJson<SubstitutionResponse>('/foods/substitutions', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function runEvaluation(payload: EvaluationRunRequest = {}) {
  return requestJson<EvaluationRunResponse>('/evaluation/run', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
