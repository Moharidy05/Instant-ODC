import { useEffect, useMemo, useState } from 'react'
import {
  Baby,
  Beaker,
  BrandMark,
  Check,
  Document,
  Heart,
  Kidney,
  LeafPlate,
  Menu,
  Search,
  Shield,
  SwapArrows,
  Wheat,
} from './components/icons'
import {
  ClassificationBadge,
  ConfidenceMeter,
  DiseaseLayerBadge,
  EvidenceCard,
  FoodItemCard,
  SafetyAlert,
  type Evidence,
  type FoodItem,
} from './components/library'
import {
  cautionFoods,
  encouragedFoods,
  evidence as mockEvidence,
  limitFoods,
  trustMetrics,
} from './data'
import {
  askFoodSafety,
  getFoodGuidanceList,
  getLayers,
  healthCheck,
  runEvaluation,
  searchEvidence,
} from './lib/api'
import { evidenceChunkToCard, guidanceItemToFoodCard, parseAnswer } from './lib/mappers'
import type {
  AskResponse,
  EvaluationRunResponse,
  EvidenceChunk,
  FoodGuidanceListResponse,
  HealthResponse,
  LayerRow,
} from './types/api'

const NAV = ['Home', 'Food Check', 'Food List', 'Evidence', 'Disease Layers', 'Evaluation']
const NAV_IDS = ['home', 'food-check', 'food-list', 'evidence', 'disease-layers', 'evaluation']

const EXAMPLES = [
  'Can a person with diabetes drink orange juice?',
  'Are legumes encouraged for diabetes?',
  'Is water better than soda for diabetes?',
  'Are processed foods recommended for people with diabetes?',
  'How much insulin should I take after eating rice?',
  'I have diabetes and kidney disease. Can I eat bananas daily?',
  'Who won the world cup?',
]

const FALLBACK_LAYERS: LayerRow[] = [
  { layer: 'diabetes', active: true, required_documents: ['ada_standards_2026_section_5'], description: 'Grounded in ADA Standards of Care 2026 nutrition guidance.' },
  { layer: 'diabetes_ckd', active: false, required_documents: [], description: 'Inactive until CKD guideline evidence is indexed.' },
  { layer: 'diabetes_cvd', active: false, required_documents: [], description: 'Inactive until cardiovascular guideline evidence is indexed.' },
  { layer: 'diabetes_pregnancy', active: false, required_documents: [], description: 'Inactive until pregnancy guideline evidence is indexed.' },
  { layer: 'diabetes_hypertension', active: false, required_documents: [], description: 'Inactive until hypertension guideline evidence is indexed.' },
]

const LAYER_LABELS: Record<string, string> = {
  diabetes: 'Diabetes',
  diabetes_ckd: 'Diabetes + Kidney Disease',
  diabetes_cvd: 'Diabetes + Cardiovascular Disease',
  diabetes_pregnancy: 'Diabetes + Pregnancy',
  diabetes_hypertension: 'Diabetes + Hypertension',
}

const LAYER_ICON = {
  diabetes: Shield,
  diabetes_ckd: Kidney,
  diabetes_cvd: Heart,
  diabetes_pregnancy: Baby,
  diabetes_hypertension: Heart,
} as const

const FOOD_ICON = {
  encouraged: LeafPlate,
  caution: Wheat,
  limit: Beaker,
} as const

const t = {
  en: {
    dir: 'ltr' as const,
    heroLabel: 'Evidence-based food safety',
    heroTitle: 'Ask what you can eat with diabetes.',
    heroSub: 'Get clear food guidance, safer alternatives, and citations from official clinical guidelines.',
    ctaAsk: 'Ask about a food',
    ctaList: 'View food guidance list',
    checkCta: 'Check Food Safety',
    dashTitle: 'The clinical food-safety workspace',
    dashSub: 'Set the patient context, ask about a food, and see exactly which guideline evidence supports every answer.',
    patientContext: 'Patient context',
    diseaseLayer: 'Disease layer',
    language: 'Language',
    askQuestion: 'Ask a food question',
    inputPh: 'Ask about a food or drink...',
    examples: 'Try an example',
    result: 'Food safety result',
    shortAnswer: 'Short answer',
    why: 'Why',
    betterAlt: 'Better alternative',
    safetyNote: 'Safety note',
    retrieved: 'Retrieved evidence',
  },
  ar: {
    dir: 'rtl' as const,
    heroLabel: 'أمان غذائي قائم على الأدلة',
    heroTitle: 'اسأل عن أكلك، واعرف الأنسب لك بدليل واضح وبدائل آمنة.',
    heroSub: 'احصل على إرشادات غذائية واضحة وبدائل أكثر أمانًا واستشهادات من الأدلة السريرية الرسمية.',
    ctaAsk: 'اسأل عن طعام',
    ctaList: 'عرض قائمة الإرشادات',
    checkCta: 'افحص أمان الطعام',
    dashTitle: 'مساحة العمل السريرية لأمان الطعام',
    dashSub: 'حدّد حالة المريض، اسأل عن طعام، وشاهد بالضبط أي دليل إرشادي يدعم كل إجابة.',
    patientContext: 'حالة المريض',
    diseaseLayer: 'طبقة المرض',
    language: 'اللغة',
    askQuestion: 'اطرح سؤالًا عن طعام',
    inputPh: 'اسأل عن طعام أو شراب...',
    examples: 'جرّب مثالًا',
    result: 'نتيجة أمان الطعام',
    shortAnswer: 'إجابة موجزة',
    why: 'لماذا',
    betterAlt: 'بديل أفضل',
    safetyNote: 'ملاحظة أمان',
    retrieved: 'الأدلة المسترجَعة',
  },
}

export default function App() {
  const [lang, setLang] = useState<'en' | 'ar'>('en')
  const [menuOpen, setMenuOpen] = useState(false)
  const [activeLayer, setActiveLayer] = useState('diabetes')
  const [query, setQuery] = useState(EXAMPLES[0])
  const [topK, setTopK] = useState(5)
  const [foodTab, setFoodTab] = useState<'encouraged' | 'caution' | 'limit'>('encouraged')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [layers, setLayers] = useState<LayerRow[]>(FALLBACK_LAYERS)
  const [guidance, setGuidance] = useState<FoodGuidanceListResponse | null>(null)
  const [askResult, setAskResult] = useState<AskResponse | null>(null)
  const [askLoading, setAskLoading] = useState(false)
  const [askError, setAskError] = useState('')
  const [offline, setOffline] = useState(false)
  const [evidenceQuery, setEvidenceQuery] = useState('Can a person with diabetes drink orange juice?')
  const [evidenceTopK, setEvidenceTopK] = useState(5)
  const [evidenceResults, setEvidenceResults] = useState<EvidenceChunk[]>([])
  const [evidenceLoading, setEvidenceLoading] = useState(false)
  const [evidenceError, setEvidenceError] = useState('')
  const [evaluation, setEvaluation] = useState<EvaluationRunResponse | null>(null)
  const [evaluationLoading, setEvaluationLoading] = useState(false)

  const L = t[lang]

  useEffect(() => {
    void Promise.all([
      healthCheck()
        .then((data) => {
          setHealth(data)
          setOffline(false)
        })
        .catch(() => setOffline(true)),
      getLayers()
        .then((data) => setLayers(data.layers))
        .catch(() => setOffline(true)),
      getFoodGuidanceList('diabetes')
        .then((data) => setGuidance(data))
        .catch(() => setOffline(true)),
    ])
  }, [])

  const parsedAnswer = useMemo(
    () => (askResult ? parseAnswer(askResult.answer, askResult.safety.safety_label) : null),
    [askResult],
  )

  const resultClassification = parsedAnswer?.classification ?? 'limit'
  const resultEvidenceCards = (askResult?.retrieval.chunks ?? []).map(evidenceChunkToCard)

  const foods = useMemo<FoodItem[]>(() => {
    if (!guidance || offline) {
      return { encouraged: encouragedFoods, caution: cautionFoods, limit: limitFoods }[foodTab]
    }
    const source =
      foodTab === 'encouraged'
        ? guidance.encouraged
        : foodTab === 'caution'
          ? guidance.suitable_with_caution
          : guidance.better_to_limit
    return source.map((item) => ({
      ...guidanceItemToFoodCard(item, foodTab),
      Icon: FOOD_ICON[foodTab],
    }))
  }, [foodTab, guidance, offline])

  const explorerCards: Evidence[] =
    evidenceResults.length > 0 ? evidenceResults.map(evidenceChunkToCard) : mockEvidence

  const healthRuntime = health?.readiness?.runtime
  const healthConfig = health?.readiness?.configuration
  const backendOnline = health?.status === 'ok' && !offline

  const runCheck = async (nextQuery = query) => {
    setQuery(nextQuery)
    setAskLoading(true)
    setAskError('')
    try {
      const response = await askFoodSafety({
        question: nextQuery,
        disease_layer: activeLayer,
        language: lang,
        top_k: topK,
        show_chunks: true,
      })
      setAskResult(response)
      setOffline(false)
    } catch (error) {
      setAskError(error instanceof Error ? error.message : 'Backend request failed')
      setOffline(true)
    } finally {
      setAskLoading(false)
    }
  }

  const runEvidenceSearch = async () => {
    setEvidenceLoading(true)
    setEvidenceError('')
    try {
      const response = await searchEvidence({
        query: evidenceQuery,
        disease_layer: activeLayer,
        clinical_topic: 'diabetes_food_safety',
        top_k: evidenceTopK,
      })
      setEvidenceResults(response.chunks)
      setOffline(false)
    } catch (error) {
      setEvidenceError(error instanceof Error ? error.message : 'Evidence search failed')
      setOffline(true)
    } finally {
      setEvidenceLoading(false)
    }
  }

  const runEval = async () => {
    setEvaluationLoading(true)
    try {
      const response = await runEvaluation({ limit: 10, disease_layer: activeLayer })
      setEvaluation(response)
      setOffline(false)
    } catch {
      setOffline(true)
    } finally {
      setEvaluationLoading(false)
    }
  }

  return (
    <div dir={L.dir} className="min-h-screen bg-white text-navy-text">
      <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 backdrop-blur">
        <div className="hidden bg-navy text-white lg:block">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-2 text-[12px]">
            <div className="flex items-center gap-6 text-white/75">
              <TrustItem icon={<Check width={14} height={14} />} text="Evidence-based guidance" />
              <TrustItem icon={<Document width={14} height={14} />} text="Official guideline citations" />
              <TrustItem
                icon={<span className={`h-1.5 w-1.5 rounded-full ${backendOnline ? 'bg-teal' : 'bg-amber'}`} />}
                text={backendOnline ? 'Backend online' : 'Backend offline'}
              />
            </div>
            <span className="text-white/60">
              {healthRuntime?.retrieval_mode ?? 'local demo'} · Gemini configured:{' '}
              {String(Boolean(healthConfig?.gemini_configured))}
            </span>
          </div>
        </div>

        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
          <a href="#home" className="flex items-center gap-3">
            <BrandMark width={40} height={40} />
            <span className="leading-tight">
              <span className="block font-display text-[16px] font-extrabold text-navy">
                Diabetes Food Safety Navigator
              </span>
              <span className="block text-[11px] font-medium text-slate-400" dir="rtl">
                مساعد أمان الطعام لمرضى السكري
              </span>
            </span>
          </a>

          <nav className="hidden items-center gap-7 xl:flex">
            {NAV.map((item, i) => (
              <a key={item} href={`#${NAV_IDS[i]}`} className="text-[14px] font-medium text-slate-600 transition-colors hover:text-teal-600">
                {item}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <span className={`hidden rounded-lg px-3 py-2 text-[12px] font-semibold sm:inline-block ${backendOnline ? 'bg-cyan-soft text-teal-600' : 'bg-amber/10 text-amber'}`}>
              {backendOnline ? 'Backend online' : 'Backend offline - showing mock demo data'}
            </span>
            <a href="#food-check" className="hidden rounded-lg bg-teal px-4 py-2.5 text-[14px] font-semibold text-navy shadow-sm transition-all hover:bg-teal-600 hover:text-white sm:inline-block">
              Check Food Safety
            </a>
            <button onClick={() => setMenuOpen((v) => !v)} className="rounded-lg border border-slate-200 p-2 text-slate-600 xl:hidden" aria-label="Toggle menu">
              <Menu width={22} height={22} />
            </button>
          </div>
        </div>

        {menuOpen && (
          <div className="border-t border-slate-200 bg-white px-6 py-4 xl:hidden">
            <div className="flex flex-col gap-1">
              {NAV.map((item, i) => (
                <a key={item} href={`#${NAV_IDS[i]}`} onClick={() => setMenuOpen(false)} className="rounded-lg px-3 py-2.5 text-[15px] font-medium text-slate-700 hover:bg-slate-50">
                  {item}
                </a>
              ))}
            </div>
          </div>
        )}
      </header>

      <section id="home" className="relative overflow-hidden bg-grey-light">
        <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-6 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:py-24">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-cyan-soft px-3.5 py-1.5 text-[12px] font-bold uppercase tracking-wider text-teal-600">
              <span className="h-1.5 w-1.5 rounded-full bg-teal" />
              {L.heroLabel}
            </span>
            <h1 className="mt-5 font-display text-[40px] font-extrabold leading-[1.08] tracking-tight text-navy sm:text-[52px]">
              {L.heroTitle}
            </h1>
            <p className="mt-5 max-w-xl text-[17px] leading-relaxed text-slate-600">{L.heroSub}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a href="#food-check" className="inline-flex items-center gap-2 rounded-xl bg-navy px-6 py-3.5 text-[15px] font-semibold text-white shadow-lg shadow-navy/20 transition-transform hover:-translate-y-0.5">
                <Search width={18} height={18} />
                {L.ctaAsk}
              </a>
              <a href="#food-list" className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-6 py-3.5 text-[15px] font-semibold text-navy transition-colors hover:border-teal hover:text-teal-600">
                {L.ctaList}
              </a>
            </div>
            <div className="mt-9 flex items-center gap-6 text-[13px] text-slate-500">
              <span className="flex items-center gap-2"><Shield width={16} height={16} className="text-teal-600" /> Evidence-first</span>
              <span className="flex items-center gap-2"><Document width={16} height={16} className="text-teal-600" /> Cited answers</span>
              <span className="flex items-center gap-2"><Check width={16} height={16} className="text-teal-600" /> Scope guarded</span>
            </div>
          </div>

          <div className="relative rounded-[24px] border border-slate-200 bg-white p-6 shadow-[0_40px_80px_-40px_rgba(7,30,61,0.4)]">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center gap-2 text-[13px] font-semibold text-slate-500">
                <BrandMark width={26} height={26} /> Food Safety Check
              </div>
              <DiseaseLayerBadge label="Diabetes" active />
            </div>
            <div className="mt-5 flex justify-end">
              <p className="max-w-[80%] rounded-2xl rounded-tr-sm bg-navy px-4 py-2.5 text-[14px] font-medium text-white">
                Can I drink orange juice?
              </p>
            </div>
            <div className="mt-4 rounded-2xl border border-slate-200 bg-grey-light/60 p-4">
              <ClassificationBadge kind="limit" />
              <p className="mt-3 text-[14px] font-semibold text-navy">Better to choose whole fruit or water.</p>
              <p className="mt-1.5 text-[13px] leading-relaxed text-slate-600">
                Beverage questions are routed to retrieved guideline chunks before generation.
              </p>
              <div className="mt-3 flex items-center gap-2 rounded-lg bg-cyan-soft px-3 py-2">
                <SwapArrows width={16} height={16} className="text-teal-600" />
                <span className="text-[13px] font-medium text-teal-600">Try: whole fruit or water</span>
              </div>
            </div>
            <div className="mt-4 flex items-start gap-2 rounded-xl border border-slate-200 bg-white p-3">
              <Document width={16} height={16} className="mt-0.5 text-slate-400" />
              <p className="text-[12px] leading-relaxed text-slate-500">
                <span className="font-semibold text-slate-600">Evidence:</span> Retrieved chunks, citation validation, and unsupported claim checks are displayed in the workspace.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto -mt-8 max-w-7xl px-6">
        <div className="grid gap-5 md:grid-cols-3">
          <FeatureCard icon={<LeafPlate width={24} height={24} />} title="Food Safety Check" text="Ask if a food or drink is encouraged, suitable with caution, or better to limit." />
          <FeatureCard icon={<SwapArrows width={24} height={24} />} title="Safer Alternatives" text="If a food is not preferred, get a close alternative supported by evidence." />
          <FeatureCard icon={<Document width={24} height={24} />} title="Evidence Panel" text="See the retrieved guideline chunks before the answer is generated." />
        </div>
      </section>

      <section id="food-check" className="mx-auto max-w-7xl px-6 py-20">
        <SectionHead eyebrow="Workspace" title={L.dashTitle} sub={L.dashSub} langToggle={<LangToggle lang={lang} setLang={setLang} label={L.language} />} />

        <div className="mt-10 grid gap-6 lg:grid-cols-[300px_1fr_340px]">
          <aside className="flex flex-col gap-5">
            <Panel title={L.patientContext}>
              <p className="mb-3 text-[12px] font-semibold uppercase tracking-wide text-slate-400">{L.diseaseLayer}</p>
              <div className="flex flex-col gap-2">
                {layers.map((layer) => (
                  <button key={layer.layer} onClick={() => setActiveLayer(layer.layer)} className={`flex items-center justify-between rounded-xl border px-3.5 py-3 text-left transition-all ${activeLayer === layer.layer ? 'border-teal bg-cyan-soft' : 'border-slate-200 hover:border-teal/60'}`}>
                    <span className="text-[13px] font-semibold text-navy">{LAYER_LABELS[layer.layer] ?? layer.layer}</span>
                    <DiseaseLayerBadge label={layer.active ? 'Active' : 'Inactive'} active={layer.active} />
                  </button>
                ))}
              </div>
              <label className="mt-5 block text-[12px] font-semibold uppercase tracking-wide text-slate-400">Top-k evidence chunks</label>
              <input type="range" min={1} max={10} value={topK} onChange={(event) => setTopK(Number(event.target.value))} className="mt-2 w-full accent-teal" />
              <p className="mt-1 font-mono text-[12px] text-slate-500">{topK} chunks</p>
            </Panel>
            <SafetyAlert title="Not medical advice">
              This tool provides general, evidence-based food guidance. It is not a personalized diet plan or medical prescription.
            </SafetyAlert>
          </aside>

          <div className="flex flex-col gap-6">
            <Panel title={L.askQuestion}>
              <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 focus-within:border-teal focus-within:ring-2 focus-within:ring-teal/20">
                <Search width={20} height={20} className="text-slate-400" />
                <input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') void runCheck(query) }} placeholder={L.inputPh} className="w-full bg-transparent text-[15px] text-navy outline-none placeholder:text-slate-400" />
              </div>
              <p className="mb-2 mt-4 text-[12px] font-semibold uppercase tracking-wide text-slate-400">{L.examples}</p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLES.map((chip) => (
                  <button key={chip} onClick={() => void runCheck(chip)} className={`rounded-full border px-3.5 py-1.5 text-[13px] font-medium transition-colors ${query === chip ? 'border-teal bg-cyan-soft text-teal-600' : 'border-slate-200 text-slate-600 hover:border-teal/60 hover:text-teal-600'}`}>
                    {chip}
                  </button>
                ))}
              </div>
              <button onClick={() => void runCheck(query)} disabled={askLoading} className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-navy px-6 py-3.5 text-[15px] font-semibold text-white transition-transform hover:-translate-y-0.5 disabled:cursor-wait disabled:opacity-70 sm:w-auto">
                <Shield width={18} height={18} />
                {askLoading ? 'Checking...' : L.checkCta}
              </button>
              {askError && <p className="mt-3 rounded-lg bg-amber/10 px-3 py-2 text-[13px] font-medium text-amber">Backend offline - showing mock demo data. {askError}</p>}
            </Panel>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_20px_50px_-40px_rgba(7,30,61,0.5)]">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
                <p className="text-[13px] font-semibold uppercase tracking-wide text-slate-400">{L.result}</p>
                <ClassificationBadge kind={resultClassification} arabic={lang === 'ar'} />
              </div>

              {askResult ? (
                <>
                  <ResultBlock label="Safety label" strong>{String(askResult.safety.safety_label ?? 'unknown')} - {String(askResult.safety.reason ?? '')}</ResultBlock>
                  <ResultBlock label="Confidence">{askResult.retrieval.confidence} · top score {askResult.retrieval.top_score.toFixed(3)}</ResultBlock>
                  <ResultBlock label={L.shortAnswer} strong>{parsedAnswer?.shortAnswer}</ResultBlock>
                  {parsedAnswer?.why && <ResultBlock label={L.why}>{parsedAnswer.why}</ResultBlock>}
                  {parsedAnswer?.betterAlternative && (
                    <div className="mt-4 flex items-start gap-3 rounded-xl bg-cyan-soft p-4">
                      <SwapArrows width={20} height={20} className="mt-0.5 text-teal-600" />
                      <div>
                        <p className="text-[12px] font-semibold uppercase tracking-wide text-teal-600">{L.betterAlt}</p>
                        <p className="mt-0.5 text-[14px] font-medium text-navy">{parsedAnswer.betterAlternative}</p>
                      </div>
                    </div>
                  )}
                  {parsedAnswer?.evidenceExcerpt && <ResultBlock label="Evidence excerpt">{parsedAnswer.evidenceExcerpt}</ResultBlock>}
                  {parsedAnswer?.citations && <ResultBlock label="Citations">{parsedAnswer.citations}</ResultBlock>}
                  {askResult.substitutions.length > 0 && <ResultBlock label="Substitutions">{askResult.substitutions.map((item) => item.alternative).join('; ')}</ResultBlock>}
                  {askResult.unsupported_claims.length > 0 && <ResultBlock label="Unsupported claims">{askResult.unsupported_claims.map((claim) => claim.sentence).join(' | ')}</ResultBlock>}
                  <ResultBlock label="Citation validation">{JSON.stringify(askResult.citation_validation)}</ResultBlock>
                  <div className="mt-4">
                    <SafetyAlert tone={resultClassification === 'refused' ? 'refusal' : 'note'} title={L.safetyNote}>
                      {parsedAnswer?.safetyNote || 'Consult a qualified clinician or registered dietitian for personalized care.'}
                    </SafetyAlert>
                  </div>
                </>
              ) : (
                <>
                  <ResultBlock label={L.shortAnswer} strong>Better to limit orange juice.</ResultBlock>
                  <ResultBlock label={L.why}>Backend offline - showing mock demo data until the API responds.</ResultBlock>
                  <div className="mt-4">
                    <SafetyAlert title={L.safetyNote}>This is not a personalized diet plan or medical prescription.</SafetyAlert>
                  </div>
                </>
              )}
            </div>
          </div>

          <aside>
            <div className="mb-3 flex items-center justify-between">
              <p className="text-[13px] font-semibold uppercase tracking-wide text-slate-400">{L.retrieved}</p>
              <span className="rounded-md bg-slate-100 px-2 py-0.5 font-mono text-[11px] text-slate-500">{resultEvidenceCards.length || mockEvidence.length} chunks</span>
            </div>
            <div className="flex flex-col gap-3">
              {(resultEvidenceCards.length > 0 ? resultEvidenceCards : mockEvidence).map((item) => <EvidenceCard key={item.chunk} e={item} />)}
            </div>
          </aside>
        </div>
      </section>

      <section id="food-list" className="bg-grey-light py-20">
        <div className="mx-auto max-w-7xl px-6">
          <SectionHead eyebrow="Reference" title="Food guidance list" sub="Browse foods sorted by how they fit an evidence-based diabetes eating pattern." />
          <div className="mt-8 inline-flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-white p-1">
            {([['encouraged', 'Encouraged'], ['caution', 'Suitable with Caution'], ['limit', 'Better to Limit']] as const).map(([key, label]) => (
              <button key={key} onClick={() => setFoodTab(key)} className={`rounded-lg px-4 py-2.5 text-[14px] font-semibold transition-colors ${foodTab === key ? 'bg-navy text-white' : 'text-slate-600 hover:text-navy'}`}>
                {label}
              </button>
            ))}
          </div>
          {offline && <p className="mt-4 rounded-lg bg-amber/10 px-3 py-2 text-[13px] font-medium text-amber">Backend offline - showing mock demo data</p>}
          <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {foods.map((item) => <FoodItemCard key={item.name} item={item} />)}
          </div>
        </div>
      </section>

      <section id="evidence" className="mx-auto max-w-7xl px-6 py-20">
        <SectionHead eyebrow="Transparency" title="Evidence explorer" sub="Every answer is grounded in retrieved guideline chunks - inspect the source before you trust the result." />
        <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-5">
          <div className="grid gap-3 md:grid-cols-[1fr_180px_120px]">
            <input value={evidenceQuery} onChange={(event) => setEvidenceQuery(event.target.value)} className="rounded-xl border border-slate-200 px-4 py-3 text-[14px] outline-none focus:border-teal" placeholder="Search retrieved evidence" />
            <select value={activeLayer} onChange={(event) => setActiveLayer(event.target.value)} className="rounded-xl border border-slate-200 px-3 py-3 text-[14px] outline-none focus:border-teal">
              {layers.map((layer) => <option key={layer.layer} value={layer.layer}>{LAYER_LABELS[layer.layer] ?? layer.layer}</option>)}
            </select>
            <input type="number" min={1} max={25} value={evidenceTopK} onChange={(event) => setEvidenceTopK(Number(event.target.value))} className="rounded-xl border border-slate-200 px-3 py-3 text-[14px] outline-none focus:border-teal" />
          </div>
          <button onClick={() => void runEvidenceSearch()} disabled={evidenceLoading} className="mt-4 inline-flex items-center gap-2 rounded-xl bg-navy px-5 py-3 text-[14px] font-semibold text-white disabled:cursor-wait disabled:opacity-70">
            <Search width={16} height={16} />
            {evidenceLoading ? 'Searching...' : 'Search evidence'}
          </button>
          {evidenceError && <p className="mt-3 rounded-lg bg-amber/10 px-3 py-2 text-[13px] font-medium text-amber">Backend offline - showing mock demo data. {evidenceError}</p>}
        </div>
        <div className="mt-8 grid gap-5 lg:grid-cols-3">
          {explorerCards.map((item) => <EvidenceCard key={item.chunk} e={item} />)}
        </div>
      </section>

      <section id="disease-layers" className="bg-navy py-20 text-white">
        <div className="mx-auto max-w-7xl px-6">
          <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3.5 py-1.5 text-[12px] font-bold uppercase tracking-wider text-teal">Clinical rules engine</span>
          <h2 className="mt-4 max-w-2xl font-display text-[34px] font-extrabold leading-tight text-white">Disease layers</h2>
          <p className="mt-3 max-w-2xl text-[16px] leading-relaxed text-white/70">
            Each layer applies a distinct set of guideline-derived rules. Layers activate only when their supporting clinical guideline is loaded and validated.
          </p>
          <div className="mt-10 grid gap-5 md:grid-cols-2 lg:grid-cols-5">
            {layers.map((layer) => {
              const Icon = LAYER_ICON[layer.layer as keyof typeof LAYER_ICON] ?? Shield
              return (
                <article key={layer.layer} className={`flex flex-col rounded-2xl border p-6 ${layer.active ? 'border-teal/40 bg-white/[0.07]' : 'border-white/10 bg-white/[0.03]'}`}>
                  <span className="flex h-12 w-12 items-center justify-center rounded-xl" style={{ backgroundColor: layer.active ? 'rgba(34,199,184,0.16)' : 'rgba(255,255,255,0.06)', color: layer.active ? '#22c7b8' : 'rgba(255,255,255,0.55)' }}>
                    <Icon width={24} height={24} />
                  </span>
                  <h3 className="mt-4 font-display text-[17px] font-bold text-white">{LAYER_LABELS[layer.layer] ?? layer.layer}</h3>
                  <p className="mt-2 flex-1 text-[13px] leading-relaxed text-white/60">{layer.description || 'Inactive until supporting guideline evidence is indexed.'}</p>
                  <div className="mt-4 flex items-center justify-between border-t border-white/10 pt-4">
                    <span className="inline-flex items-center gap-1.5 text-[12px] font-semibold" style={{ color: layer.active ? '#22c7b8' : 'rgba(255,255,255,0.5)' }}>
                      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: layer.active ? '#22c7b8' : 'rgba(255,255,255,0.4)' }} />
                      {layer.active ? 'Active' : 'Inactive'}
                    </span>
                    <span className="text-[11px] text-white/45">{layer.required_documents.length ? 'Indexed' : 'Requires guideline'}</span>
                  </div>
                </article>
              )
            })}
          </div>
        </div>
      </section>

      <section id="evaluation" className="mx-auto max-w-7xl px-6 py-20">
        <SectionHead eyebrow="Quality & trust" title="How the system is evaluated" sub="Continuous checks keep answers grounded, cited, and safe - measured against the source guidelines." />
        <button onClick={() => void runEval()} disabled={evaluationLoading} className="mt-8 inline-flex items-center gap-2 rounded-xl bg-navy px-5 py-3 text-[14px] font-semibold text-white disabled:cursor-wait disabled:opacity-70">
          <Shield width={16} height={16} />
          {evaluationLoading ? 'Running...' : 'Run backend evaluation'}
        </button>
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {evaluation
            ? [
                ['Retrieval Precision@5', evaluation.metrics.retrieval_precision_at_5],
                ['Citation accuracy', evaluation.metrics.citation_accuracy],
                ['Refusal behavior', evaluation.metrics.refusal_accuracy],
                ['Average retrieval score', evaluation.metrics.average_retrieval_score],
              ].map(([label, value]) => (
                <ConfidenceMeter key={String(label)} label={String(label)} value={Math.round(Number(value) * 100)} caption={`Total queries: ${evaluation.metrics.total_queries}. Unsupported claims: ${evaluation.metrics.unsupported_claim_count}.`} />
              ))
            : trustMetrics.map((metric) => <ConfidenceMeter key={metric.label} label={metric.label} value={metric.value} caption={metric.caption} />)}
          <div className="flex flex-col justify-center rounded-2xl border border-teal/30 bg-cyan-soft p-6">
            <Shield width={28} height={28} className="text-teal-600" />
            <p className="mt-3 font-display text-[16px] font-bold text-navy">Evidence-first by design</p>
            <p className="mt-1.5 text-[13px] leading-relaxed text-slate-600">No answer is shown until supporting guideline evidence has been retrieved and matched.</p>
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-200 bg-grey-light">
        <div className="mx-auto max-w-7xl px-6 py-14">
          <div className="grid gap-10 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
            <div>
              <div className="flex items-center gap-3">
                <BrandMark width={38} height={38} />
                <span className="font-display text-[15px] font-extrabold text-navy">Diabetes Food Safety Navigator</span>
              </div>
              <p className="mt-4 max-w-sm text-[13px] leading-relaxed text-slate-500">
                Evidence-based food guidance grounded in official clinical guidelines. For education and general information only - not a substitute for professional medical advice.
              </p>
              <p className="mt-3 text-[12px] font-medium text-slate-400" dir="rtl">مساعد أمان الطعام لمرضى السكري</p>
            </div>
            <FooterCol title="Product" links={['Food Check', 'Food List', 'Evidence', 'Disease Layers']} />
            <FooterCol title="Resources" links={['Docs', 'Guidelines', 'Methodology', 'Evaluation']} />
            <FooterCol title="Company" links={['Contact', 'Privacy', 'Terms', 'Accessibility']} />
          </div>
          <div className="mt-12 flex flex-col items-start justify-between gap-4 border-t border-slate-200 pt-6 text-[12px] text-slate-400 sm:flex-row sm:items-center">
            <p>© 2026 Diabetes Food Safety Navigator · Educational use only.</p>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 font-medium text-slate-500">
              <Check width={13} height={13} className="text-teal-600" /> Evidence-based guidance
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}

function TrustItem({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="text-teal">{icon}</span>
      {text}
    </span>
  )
}

function FeatureCard({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <article className="group rounded-2xl border border-slate-200 bg-white p-7 shadow-[0_20px_50px_-40px_rgba(7,30,61,0.5)] transition-all hover:-translate-y-1 hover:border-teal/50">
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-soft text-teal-600 transition-colors group-hover:bg-teal group-hover:text-navy">{icon}</span>
      <h3 className="mt-5 font-display text-[19px] font-bold text-navy">{title}</h3>
      <p className="mt-2 text-[14px] leading-relaxed text-slate-600">{text}</p>
    </article>
  )
}

function SectionHead({ eyebrow, title, sub, langToggle }: { eyebrow: string; title: string; sub: string; langToggle?: React.ReactNode }) {
  return (
    <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
      <div className="max-w-2xl">
        <span className="text-[12px] font-bold uppercase tracking-[0.14em] text-teal-600">{eyebrow}</span>
        <h2 className="mt-2 font-display text-[32px] font-extrabold leading-tight tracking-tight text-navy sm:text-[36px]">{title}</h2>
        <p className="mt-3 text-[16px] leading-relaxed text-slate-600">{sub}</p>
      </div>
      {langToggle}
    </div>
  )
}

function LangToggle({ lang, setLang, label }: { lang: 'en' | 'ar'; setLang: (lang: 'en' | 'ar') => void; label: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-[12px] font-semibold uppercase tracking-wide text-slate-400">{label}</span>
      <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1">
        <button onClick={() => setLang('en')} className={`rounded-md px-3.5 py-1.5 text-[13px] font-semibold transition-colors ${lang === 'en' ? 'bg-navy text-white' : 'text-slate-500'}`}>
          English
        </button>
        <button onClick={() => setLang('ar')} className={`rounded-md px-3.5 py-1.5 text-[13px] font-semibold transition-colors ${lang === 'ar' ? 'bg-navy text-white' : 'text-slate-500'}`}>
          عربي
        </button>
      </div>
    </div>
  )
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6">
      <h3 className="mb-4 font-display text-[15px] font-bold text-navy">{title}</h3>
      {children}
    </div>
  )
}

function ResultBlock({ label, strong, children }: { label: string; strong?: boolean; children: React.ReactNode }) {
  return (
    <div className="mt-4">
      <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-1 whitespace-pre-wrap leading-relaxed ${strong ? 'text-[16px] font-semibold text-navy' : 'text-[14px] text-slate-600'}`}>{children}</p>
    </div>
  )
}

function FooterCol({ title, links }: { title: string; links: string[] }) {
  return (
    <div>
      <p className="font-display text-[13px] font-bold uppercase tracking-wide text-navy">{title}</p>
      <ul className="mt-4 flex flex-col gap-2.5">
        {links.map((link) => (
          <li key={link}>
            <a href="#" className="text-[13px] text-slate-500 transition-colors hover:text-teal-600">{link}</a>
          </li>
        ))}
      </ul>
    </div>
  )
}
