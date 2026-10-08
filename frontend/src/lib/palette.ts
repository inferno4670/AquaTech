/**
 * The land-and-sea palette, and the single place its hexes are written down.
 *
 * These values are not invented: they are the custom properties of the authored Field
 * Manuals showcase that the landing route renders full-bleed (see
 * `public/landing-pages/aquatrack-field-manuals.html`, `:root`). Two of the authored names
 * are misleading — its `--pink` is a gold and its `--periwinkle` is a sand — so the names
 * below describe the colour instead. `index.css` mirrors the same values for the CSS custom
 * properties; the two files have to stay in step, which is the only reason this is a list
 * of literals rather than a generated file.
 *
 * Everything the app draws outside that iframe — map paint, fish markers, chips, popups —
 * reads from here, so the books and the pages they open share one ground.
 */
export const PALETTE = {
  /** Deepest ground: the floor of the authored stage gradient. */
  inkDeep: '#1d1a15',
  /** The authored page colour. */
  ink: '#29251d',
  /** Raised surfaces inside the ink. */
  inkSoft: '#3a382b',
  /** Body copy. */
  text: '#eee2ca',
  /** Secondary copy. */
  muted: '#c5b79e',
  /** Dimmest legible copy. */
  faint: '#9e9280',
  /** Primary accent — the authored `--pink-bright`. */
  goldBright: '#dbc39c',
  /** Secondary accent — the authored `--pink`. */
  gold: '#c3a47b',
  /** Tertiary accent — the authored `--periwinkle`. */
  sand: '#b7976c',
  /** Affirmation. */
  sage: '#89946f',
  /** Caution. */
  moss: '#5f684f',
  /** Refusal, protection, restriction — the authored `--clay`. */
  clay: '#a96346',
  /** Highest-contrast surface, and map markers that must read at a glance. */
  paper: '#eadfc7',
  /** Brightest marker tier: recorded sightings on the dark basemap. */
  pale: '#f0e3c4',
  /** Warm marker tier: predicted hotspots, so they stay distinct from sightings. */
  amber: '#dcaa5e',
  /** Ink used for text and outlines drawn *on* the light tiers above. */
  onLight: '#312a21',
} as const;

/** Suitability ramp, ascending. Deliberately one hue so intensity reads as intensity. */
export const SUITABILITY_RAMP = {
  low: PALETTE.clay,
  moderate: PALETTE.sand,
  high: PALETTE.gold,
  very_high: PALETTE.goldBright,
} as const;

export type SuitabilityBand = keyof typeof SUITABILITY_RAMP;

/**
 * The authored stage background, reused verbatim so the app and the landing page sit on the
 * same ground. Kept as a CSS string rather than a Tailwind class because it is a three-layer
 * gradient, and because the landing document owns the definition.
 */
export const STAGE_BACKGROUND =
  'radial-gradient(circle at 49% 84%, rgba(117, 102, 71, .2), transparent 34%),' +
  'radial-gradient(circle at 14% 4%, rgba(100, 112, 77, .12), transparent 28%),' +
  'linear-gradient(180deg, #343025 0%, #29251d 48%, #211e18 100%)';
