import { PALETTE, SUITABILITY_RAMP } from './palette';

export function suitabilityBand(v: number): 'very_high' | 'high' | 'moderate' | 'low' {
  if (v >= 0.81) return 'very_high';
  if (v >= 0.61) return 'high';
  if (v >= 0.31) return 'moderate';
  return 'low';
}

export function bandLabel(b: 'very_high' | 'high' | 'moderate' | 'low'): string {
  return { very_high: 'Very High', high: 'High', moderate: 'Moderate', low: 'Low' }[b];
}

/** Fixed 4-step ramp used by both map paint and sidebar chips. */
export function suitabilityColor(v: number): string {
  return SUITABILITY_RAMP[suitabilityBand(v)];
}

export function bandColor(b: 'very_high' | 'high' | 'moderate' | 'low'): string {
  return SUITABILITY_RAMP[b];
}

/**
 * Legal and conservation status, drawn from the same palette as the ramp so a protected
 * species is never mistaken for a mere "low suitability" cell.
 */
export function statusColorForSpecies(legal: string, conservation: string): { color: string; label: string } {
  if (
    legal === 'protected' ||
    legal === 'restricted' ||
    conservation === 'endangered' ||
    conservation === 'critically_endangered'
  ) {
    return { color: PALETTE.clay, label: 'PROTECTED / RESTRICTED' };
  }
  if (legal === 'regulated') {
    return { color: PALETTE.sand, label: 'REGULATED' };
  }
  if (conservation === 'near_threatened' || conservation === 'vulnerable') {
    return { color: PALETTE.gold, label: 'CONSERVATION WATCH' };
  }
  return { color: PALETTE.sage, label: 'OPEN' };
}

export const DISCLAIMER =
  'AquaTrack provides probabilistic habitat estimates based on environmental and historical data. ' +
  'It does not guarantee fish presence and is not a navigation, maritime safety or legal-compliance system. ' +
  'Users remain responsible for following applicable fishing laws, protected-area rules and safety procedures.';
