export interface TimeSnapshot {
  snapshot_id: number;
  year: number;
  era: 'BC' | 'AD';
  sort_year: number;
  label: string | null;
}

export interface Nation {
  id: number;
  name: string;
  display_name: string | null;
  color: string;
  wiki_url?: string | null;
}

export interface NationDetails {
  id: number;
  name: string;
  display_name: string | null;
  color: string;
  wiki_url: string | null;
  founded: string | null;
  description: string | null;
  ruler_title: string | null;
  ruler_name: string | null;
  ruler_wiki_url: string | null;
  reign_start: string | null;
  reign_end: string | null;
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
