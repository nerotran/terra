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
