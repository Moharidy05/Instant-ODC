import {
  Apple,
  Beaker,
  Droplet,
  LeafPlate,
  Wheat,
  Sparkle,
} from './components/icons'
import type { Evidence, FoodItem } from './components/library'

export const encouragedFoods: FoodItem[] = [
  {
    name: 'Nonstarchy vegetables',
    kind: 'encouraged',
    reason: 'High fiber and low glycemic impact. Fill half the plate at meals.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: LeafPlate,
  },
  {
    name: 'Legumes',
    kind: 'encouraged',
    reason: 'Beans and lentils support steadier post-meal glucose and satiety.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: Beaker,
  },
  {
    name: 'Whole fruits',
    kind: 'encouraged',
    reason: 'Preferred over juice — the fiber slows sugar absorption.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: Apple,
  },
  {
    name: 'Water',
    kind: 'encouraged',
    reason: 'The default beverage. No added sugar and no glycemic load.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: Droplet,
  },
  {
    name: 'Plant-based proteins',
    kind: 'encouraged',
    reason: 'Tofu, tempeh and legumes support cardiometabolic health.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: Sparkle,
  },
  {
    name: 'Whole grains',
    kind: 'encouraged',
    reason: 'Choose intact grains over refined for a lower glycemic response.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: Wheat,
  },
  {
    name: 'Nuts and seeds',
    kind: 'encouraged',
    reason: 'Unsalted portions add healthy fats with minimal glucose effect.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: Sparkle,
  },
]

export const cautionFoods: FoodItem[] = [
  {
    name: 'Brown rice',
    kind: 'caution',
    reason: 'A whole grain, but portion size still affects glucose — measure servings.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: Wheat,
  },
  {
    name: 'Starchy vegetables',
    kind: 'caution',
    reason: 'Potatoes and corn count toward carbohydrates. Watch portions.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: LeafPlate,
  },
  {
    name: 'Dried fruit',
    kind: 'caution',
    reason: 'Concentrated natural sugars — keep to small measured portions.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: Apple,
  },
  {
    name: 'Low-fat dairy',
    kind: 'caution',
    reason: 'Contains lactose. Unsweetened options fit better into a plan.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: Droplet,
  },
]

export const limitFoods: FoodItem[] = [
  {
    name: 'Sugary drinks',
    kind: 'limit',
    reason: 'Rapid glucose spikes with little nutrition. Replace with water.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: Droplet,
  },
  {
    name: 'Fruit juices',
    kind: 'limit',
    reason: 'Sugar without the fiber of whole fruit. Prefer whole fruit or water.',
    citation: 'ADA 2026 · §5, p.5',
    layer: 'Diabetes',
    Icon: Apple,
  },
  {
    name: 'Sweets',
    kind: 'limit',
    reason: 'Added sugars raise glucose quickly and add little nutritional value.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: Sparkle,
  },
  {
    name: 'Refined grains',
    kind: 'limit',
    reason: 'White bread and pasta digest fast — choose whole-grain versions.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: Wheat,
  },
  {
    name: 'Processed foods',
    kind: 'limit',
    reason: 'Often high in refined carbs, sodium and added sugars.',
    citation: 'ADA 2026 · §5',
    layer: 'Diabetes',
    Icon: Beaker,
  },
  {
    name: 'High-sodium foods',
    kind: 'limit',
    reason: 'Excess sodium raises cardiovascular risk in diabetes.',
    citation: 'ADA 2026 · §10',
    layer: 'Diabetes',
    Icon: Beaker,
  },
]

export const evidence: Evidence[] = [
  {
    chunk: 'CHK-05-118',
    document: 'ADA Standards of Care 2026',
    section: 'Facilitating Positive Health Behaviors',
    page: 5,
    score: 0.94,
    excerpt:
      'Water is recommended as the preferred beverage. Sugar-sweetened beverages and fruit juice should be limited to reduce glycemic excursions.',
    citation: 'ADA Standards of Care 2026 · Section 5 · p.5',
  },
  {
    chunk: 'CHK-05-204',
    document: 'ADA Standards of Care 2026',
    section: 'Medical Nutrition Therapy',
    page: 42,
    score: 0.88,
    excerpt:
      'Whole fruits are preferred over juices because the accompanying fiber slows glucose absorption and improves satiety.',
    citation: 'ADA Standards of Care 2026 · Section 5 · p.42',
  },
  {
    chunk: 'CHK-05-077',
    document: 'ADA Standards of Care 2026',
    section: 'Carbohydrate Quality & Quantity',
    page: 39,
    score: 0.81,
    excerpt:
      'Emphasize nonstarchy vegetables, whole intact grains, and legumes while minimizing added sugars and refined grains.',
    citation: 'ADA Standards of Care 2026 · Section 5 · p.39',
  },
]

export const trustMetrics = [
  {
    label: 'Retrieval confidence',
    value: 94,
    caption: 'Average similarity of the top guideline chunks used to answer.',
  },
  {
    label: 'Citation accuracy',
    value: 98,
    caption: 'Answers correctly matched to the cited section and page.',
  },
  {
    label: 'Unsupported claims check',
    value: 96,
    caption: 'Statements verified against retrieved evidence before display.',
  },
  {
    label: 'Refusal behavior',
    value: 91,
    caption: 'Out-of-scope or unsafe questions correctly declined.',
  },
  {
    label: 'Evidence-first generation',
    value: 100,
    caption: 'Every answer is generated only after evidence is retrieved.',
  },
]

export const diseaseLayers = [
  {
    id: 'diabetes',
    title: 'Diabetes',
    status: 'active' as const,
    note: 'Grounded in the ADA Standards of Care 2026 nutrition guidance.',
    requirement: 'Live now',
  },
  {
    id: 'ckd',
    title: 'Diabetes + Kidney Disease',
    status: 'soon' as const,
    note: 'Adds potassium, phosphorus and protein constraints for CKD.',
    requirement: 'Requires CKD guideline',
  },
  {
    id: 'cvd',
    title: 'Diabetes + Cardiovascular Disease',
    status: 'soon' as const,
    note: 'Layers sodium and saturated-fat rules for heart health.',
    requirement: 'Requires CVD guideline',
  },
  {
    id: 'pregnancy',
    title: 'Diabetes + Pregnancy',
    status: 'soon' as const,
    note: 'Adds gestational targets and nutrient adequacy checks.',
    requirement: 'Requires pregnancy guideline',
  },
]
