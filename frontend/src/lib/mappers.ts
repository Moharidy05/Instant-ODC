import type { Classification } from '../components/library'
import type { AskResponse, EvidenceChunk, FoodGuidanceItem } from '../types/api'

export type ParsedAnswer = {
  classification: Classification
  shortAnswer: string
  why: string
  betterAlternative: string
  evidenceExcerpt: string
  citations: string
  safetyNote: string
  raw: string
}

const SECTION_NAMES = [
  'Food Safety Classification',
  'Short Answer',
  'Why',
  'Better Alternative',
  'Evidence Excerpt',
  'Citations',
  'Safety Note',
]

export function mapClassification(value: unknown): Classification {
  const normalized = String(value ?? '').trim().toLowerCase()
  if (normalized === 'encouraged') return 'encouraged'
  if (normalized === 'suitable_with_caution' || normalized === 'caution') return 'caution'
  if (normalized === 'better_to_limit' || normalized === 'limit') return 'limit'
  if (normalized === 'refused' || normalized === 'refuse') return 'refused'
  if (normalized === 'not_supported_by_retrieved_evidence' || normalized === 'insufficient') {
    return 'insufficient'
  }
  return 'insufficient'
}

export function parseAnswer(answer: AskResponse['answer'], safetyLabel?: unknown): ParsedAnswer {
  const raw = typeof answer === 'string' ? answer : JSON.stringify(answer, null, 2)
  const sections = new Map<string, string>()
  const pattern = new RegExp(`^(${SECTION_NAMES.join('|')}):\\s*$`, 'i')
  let current: string | null = null

  for (const line of raw.split(/\r?\n/)) {
    const match = line.match(pattern)
    if (match) {
      current = SECTION_NAMES.find((name) => name.toLowerCase() === match[1].toLowerCase()) ?? match[1]
      sections.set(current, '')
    } else if (current) {
      sections.set(current, `${sections.get(current) ?? ''}${line}\n`)
    }
  }

  const classificationText =
    sections.get('Food Safety Classification')?.trim().split(/\s+/)[0] ??
    (safetyLabel === 'refuse' ? 'refused' : '')

  return {
    classification: mapClassification(classificationText),
    shortAnswer: sections.get('Short Answer')?.trim() || raw,
    why: sections.get('Why')?.trim() || '',
    betterAlternative: sections.get('Better Alternative')?.trim() || '',
    evidenceExcerpt: sections.get('Evidence Excerpt')?.trim() || '',
    citations: sections.get('Citations')?.trim() || '',
    safetyNote: sections.get('Safety Note')?.trim() || '',
    raw,
  }
}

export function evidenceChunkToCard(chunk: EvidenceChunk) {
  return {
    chunk: chunk.chunk_id,
    document: chunk.document_title ?? 'Unknown document',
    section: chunk.section_title ?? 'Unknown section',
    page: chunk.page_start ?? 0,
    score: Number(chunk.similarity || chunk.rerank_score || 0),
    excerpt: chunk.content,
    citation: chunk.citation_label ?? '',
  }
}

export function guidanceItemToFoodCard(item: FoodGuidanceItem, kind: Classification) {
  return {
    name: item.food,
    kind,
    reason: item.note || 'Evidence-linked guidance from retrieved diabetes nutrition chunks.',
    citation: item.citation_label || item.evidence_chunk_id,
    layer: 'Diabetes',
  }
}
