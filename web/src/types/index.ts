export interface TimeSnapshot {
  snapshot_id: number;
  year: number;  // Signed: negative for BC, positive for AD
  label: string | null;
}

export interface Nation {
  id: number;
  name: string;
  display_name: string | null;
  color: string;
  wiki_url?: string | null;
}

export interface Ruler {
  id: number;
  name: string;
  title: string | null;
  wiki_url: string | null;
  portrait_url: string | null;
  reign_start: number;  // Signed year
  reign_end: number | null;  // Signed year, null if still reigning
}

export interface NationDetails {
  id: number;
  name: string;
  display_name: string | null;
  color: string;
  wiki_url: string | null;
  flag_url: string | null;
  founded_year: number | null;  // Signed year
  description: string | null;
  ruler: Ruler | null;
  capital: string | null;
  language: string | null;
  religion: string | null;
  population: string | null;
}

export interface Territory extends TimeSnapshot {
  nation: Nation;
  geometry: object | null;
}

export interface ApiResponse<T> {
  data: T;
  error?: string;
}

export interface BaseMap {
  type: 'FeatureCollection';
  features: BaseMapFeature[];
}

export interface BaseMapFeature {
  type: 'Feature';
  properties: object;
  geometry: object | null;
}

// Helper function to convert signed year to display string
export function yearToDisplay(year: number): string {
  if (year < 0) {
    return `${Math.abs(year)} BC`;
  } else if (year > 0) {
    return `${year} AD`;
  } else {
    return '1 BC';  // Year 0 doesn't exist historically
  }
}
