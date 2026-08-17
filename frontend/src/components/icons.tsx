import type { SVGProps } from 'react'

type IconProps = SVGProps<SVGSVGElement>

const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.7,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  viewBox: '0 0 24 24',
}

export function LeafPlate(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <path d="M12 7c2.5 1 3 3 1.5 5" />
    </svg>
  )
}

export function SwapArrows(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M4 8h13l-3-3" />
      <path d="M20 16H7l3 3" />
    </svg>
  )
}

export function Document(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M6 3h8l4 4v14H6z" />
      <path d="M14 3v4h4" />
      <path d="M9 12h6M9 15.5h6M9 8.5h2" />
    </svg>
  )
}

export function Shield(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  )
}

export function Check(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M5 12l5 5L19 7" />
    </svg>
  )
}

export function Alert(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3l9 16H3z" />
      <path d="M12 10v4M12 17h.01" />
    </svg>
  )
}

export function MinusCircle(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M8 12h8" />
    </svg>
  )
}

export function Question(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.5 9.5a2.5 2.5 0 113.5 2.3c-.8.4-1 .9-1 1.7" />
      <path d="M12 16.5h.01" />
    </svg>
  )
}

export function Beaker(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M9 3h6M10 3v6l-4.5 8a2 2 0 001.8 3h9.4a2 2 0 001.8-3L14 9V3" />
      <path d="M7.5 15h9" />
    </svg>
  )
}

export function Droplet(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3s6 6.5 6 10.5A6 6 0 016 13.5C6 9.5 12 3 12 3z" />
    </svg>
  )
}

export function Wheat(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 21V9" />
      <path d="M12 9c-2-1-3-2.5-3-4.5C11 5 12 6.5 12 9zM12 9c2-1 3-2.5 3-4.5C13 5 12 6.5 12 9z" />
      <path d="M12 14c-2-1-3-2.2-3-4 2 .3 3 1.7 3 4zM12 14c2-1 3-2.2 3-4-2 .3-3 1.7-3 4z" />
    </svg>
  )
}

export function Apple(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 8c-1.5-1.5-4-1.7-5.5 0-1.8 2-1 6 1.5 8.5 1 1 2 1.5 4 1.5s3-.5 4-1.5c2.5-2.5 3.3-6.5 1.5-8.5-1.5-1.7-4-1.5-5.5 0z" />
      <path d="M12 8c0-2 1-3.5 3-4" />
    </svg>
  )
}

export function Heart(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 20s-7-4.3-9-9c-1.2-3 .8-6 3.6-6 1.8 0 3 1 3.4 2 .4-1 1.6-2 3.4-2 2.8 0 4.8 3 3.6 6-2 4.7-9 9-9 9z" />
    </svg>
  )
}

export function Kidney(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M9 4C6 4 4 7 4 11s2 8 5 8c2 0 3-1.5 3-4 0-2 1-3 1-5s-1-6-4-6z" />
      <path d="M15 4c3 0 5 3 5 7s-2 8-5 8" opacity=".5" />
    </svg>
  )
}

export function Baby(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="7" r="3" />
      <path d="M6 21c0-4 2.7-7 6-7s6 3 6 7" />
      <path d="M10 6.5h.01M14 6.5h.01" />
    </svg>
  )
}

export function Search(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="11" cy="11" r="7" />
      <path d="M20 20l-3.5-3.5" />
    </svg>
  )
}

export function Cross(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 4v16M4 12h16" />
    </svg>
  )
}

export function Menu(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M4 7h16M4 12h16M4 17h16" />
    </svg>
  )
}

export function ChevronDown(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M6 9l6 6 6-6" />
    </svg>
  )
}

export function Sparkle(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" />
    </svg>
  )
}

/** A calm medical monogram: caduceus-free plate + leaf mark inside a rounded shield. */
export function BrandMark(props: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" {...props}>
      <rect x="1.5" y="1.5" width="37" height="37" rx="11" fill="#071e3d" />
      <circle cx="20" cy="20" r="11.5" stroke="#22c7b8" strokeWidth="1.6" />
      <circle cx="20" cy="20" r="6" stroke="#22c7b8" strokeWidth="1.6" />
      <path
        d="M20 13.5c3.2 1.3 3.8 4 1.8 6.5"
        stroke="#e9faf8"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <path d="M20 26.5v-6.5" stroke="#22c7b8" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}
