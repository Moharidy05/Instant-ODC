import type { ReactNode } from 'react'
import { Alert, Check, MinusCircle, Question, Shield, Document } from './icons'

/* ---------------------------------------------------------------- */
/* Classification badge                                             */
/* ---------------------------------------------------------------- */

export type Classification =
  | 'encouraged'
  | 'caution'
  | 'limit'
  | 'insufficient'
  | 'refused'

const CLASSIFICATION = {
  encouraged: {
    label: 'Encouraged',
    ar: 'موصى به',
    dot: '#16a34a',
    bg: '#ecfdf3',
    fg: '#166534',
    border: '#bbf7d0',
    Icon: Check,
  },
  caution: {
    label: 'Suitable with caution',
    ar: 'مناسب بحذر',
    dot: '#f59e0b',
    bg: '#fffbeb',
    fg: '#92600a',
    border: '#fde68a',
    Icon: Alert,
  },
  limit: {
    label: 'Better to limit',
    ar: 'يُفضّل تقليله',
    dot: '#dc2626',
    bg: '#fef2f2',
    fg: '#991b1b',
    border: '#fecaca',
    Icon: MinusCircle,
  },
  insufficient: {
    label: 'Insufficient evidence',
    ar: 'أدلة غير كافية',
    dot: '#64748b',
    bg: '#f1f5f9',
    fg: '#334155',
    border: '#cbd5e1',
    Icon: Question,
  },
  refused: {
    label: 'Refused',
    ar: 'مرفوض',
    dot: '#475569',
    bg: '#f8fafc',
    fg: '#1e293b',
    border: '#cbd5e1',
    Icon: Shield,
  },
} as const

export function ClassificationBadge({
  kind,
  size = 'md',
  arabic = false,
}: {
  kind: Classification
  size?: 'sm' | 'md'
  arabic?: boolean
}) {
  const c = CLASSIFICATION[kind]
  const pad = size === 'sm' ? 'px-2.5 py-1 text-[12px]' : 'px-3.5 py-1.5 text-[13px]'
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold ${pad}`}
      style={{ backgroundColor: c.bg, color: c.fg, border: `1px solid ${c.border}` }}
    >
      <c.Icon width={size === 'sm' ? 13 : 15} height={size === 'sm' ? 13 : 15} />
      {arabic ? c.ar : c.label}
    </span>
  )
}

export { CLASSIFICATION }

/* ---------------------------------------------------------------- */
/* Disease layer badge                                             */
/* ---------------------------------------------------------------- */

export function DiseaseLayerBadge({
  label,
  active = false,
}: {
  label: string
  active?: boolean
}) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold tracking-wide uppercase"
      style={
        active
          ? { backgroundColor: '#e9faf8', color: '#0f766e', border: '1px solid #99e6dd' }
          : { backgroundColor: '#f5f7fa', color: '#64748b', border: '1px solid #e2e8f0' }
      }
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: active ? '#22c7b8' : '#94a3b8' }}
      />
      {label}
    </span>
  )
}

/* ---------------------------------------------------------------- */
/* Evidence card                                                    */
/* ---------------------------------------------------------------- */

export type Evidence = {
  chunk: string
  document: string
  section: string
  page: number
  score: number
  excerpt: string
  citation: string
}

export function EvidenceCard({ e }: { e: Evidence }) {
  const pct = Math.round(e.score * 100)
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 transition-shadow hover:shadow-[0_8px_28px_-18px_rgba(7,30,61,0.4)]">
      <div className="flex items-center justify-between gap-3">
        <span className="inline-flex items-center gap-1.5 font-mono text-[11px] font-medium text-slate-500">
          <Document width={13} height={13} className="text-teal-600" />
          {e.chunk}
        </span>
        <span
          className="rounded-md px-2 py-0.5 font-mono text-[11px] font-semibold"
          style={{ backgroundColor: '#e9faf8', color: '#0f766e' }}
        >
          {pct}% match
        </span>
      </div>
      <h4 className="mt-2.5 font-display text-[14px] font-bold leading-snug text-navy">
        {e.section}
      </h4>
      <p className="mt-1 text-[12px] text-slate-500">
        {e.document} · Page {e.page}
      </p>
      <div className="mt-2.5 h-1 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, backgroundColor: '#22c7b8' }}
        />
      </div>
      <p className="mt-3 border-l-2 border-slate-200 pl-3 text-[13px] leading-relaxed text-slate-600">
        “{e.excerpt}”
      </p>
      <p className="mt-3 text-[11px] font-medium tracking-wide text-slate-400">
        {e.citation}
      </p>
    </article>
  )
}

/* ---------------------------------------------------------------- */
/* Food item card                                                   */
/* ---------------------------------------------------------------- */

export type FoodItem = {
  name: string
  kind: Classification
  reason: string
  citation: string
  layer: string
  Icon: (p: { width?: number; height?: number; className?: string }) => ReactNode
}

export function FoodItemCard({ item }: { item: FoodItem }) {
  const c = CLASSIFICATION[item.kind]
  return (
    <article className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-5 transition-all hover:-translate-y-0.5 hover:border-teal/50 hover:shadow-[0_16px_40px_-24px_rgba(7,30,61,0.45)]">
      <div className="flex items-start justify-between">
        <span
          className="flex h-11 w-11 items-center justify-center rounded-xl"
          style={{ backgroundColor: c.bg, color: c.fg }}
        >
          <item.Icon width={22} height={22} />
        </span>
        <span
          className="mt-1 h-2.5 w-2.5 rounded-full ring-4"
          style={{ backgroundColor: c.dot, ['--tw-ring-color' as string]: c.bg }}
        />
      </div>
      <h4 className="mt-4 font-display text-[16px] font-bold text-navy">{item.name}</h4>
      <p className="mt-1.5 flex-1 text-[13px] leading-relaxed text-slate-600">
        {item.reason}
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
        <span className="rounded-md bg-slate-50 px-2 py-1 font-mono text-[10.5px] text-slate-500">
          {item.citation}
        </span>
        <DiseaseLayerBadge label={item.layer} active />
      </div>
    </article>
  )
}

/* ---------------------------------------------------------------- */
/* Safety / refusal alert                                           */
/* ---------------------------------------------------------------- */

export function SafetyAlert({
  tone = 'note',
  title,
  children,
}: {
  tone?: 'note' | 'refusal'
  title: string
  children: ReactNode
}) {
  const styles =
    tone === 'refusal'
      ? { bg: '#fef2f2', border: '#fecaca', fg: '#991b1b', icon: '#dc2626' }
      : { bg: '#f5f7fa', border: '#e2e8f0', fg: '#334155', icon: '#0f766e' }
  return (
    <div
      className="flex gap-3 rounded-xl p-4"
      style={{ backgroundColor: styles.bg, border: `1px solid ${styles.border}` }}
    >
      <Shield width={20} height={20} style={{ color: styles.icon, flexShrink: 0, marginTop: 1 }} />
      <div>
        <p className="text-[13px] font-bold" style={{ color: styles.fg }}>
          {title}
        </p>
        <p className="mt-0.5 text-[12.5px] leading-relaxed" style={{ color: styles.fg, opacity: 0.85 }}>
          {children}
        </p>
      </div>
    </div>
  )
}

/* ---------------------------------------------------------------- */
/* Confidence meter                                                 */
/* ---------------------------------------------------------------- */

export function ConfidenceMeter({
  label,
  value,
  caption,
}: {
  label: string
  value: number
  caption: string
}) {
  const tone = value >= 90 ? '#16a34a' : value >= 75 ? '#22c7b8' : '#f59e0b'
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-baseline justify-between">
        <p className="text-[13px] font-semibold text-navy">{label}</p>
        <p className="font-display text-[22px] font-extrabold leading-none" style={{ color: tone }}>
          {value}
          <span className="text-[13px] font-bold">%</span>
        </p>
      </div>
      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${value}%`, backgroundColor: tone }}
        />
      </div>
      <p className="mt-2.5 text-[12px] leading-relaxed text-slate-500">{caption}</p>
    </div>
  )
}
