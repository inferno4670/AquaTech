import { SUITABILITY_RAMP } from '../lib/palette';

export function suitabilityBand(v: number): 'very_high' | 'high' | 'moderate' | 'low' {
  if (v >= 0.81) return 'very_high';
  if (v >= 0.61) return 'high';
  if (v >= 0.31) return 'moderate';
  return 'low';
}

export function bandLabel(b: 'very_high' | 'high' | 'moderate' | 'low'): string {
  return { very_high: 'Very High', high: 'High', moderate: 'Moderate', low: 'Low' }[b];
}

export function suitabilityColor(v: number): string {
  return SUITABILITY_RAMP[suitabilityBand(v)];
}

export function bandColor(b: 'very_high' | 'high' | 'moderate' | 'low'): string {
  return SUITABILITY_RAMP[b];
}
