import type { Territory, TimeSnapshot, BaseMap } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function getSnapshots(): Promise<TimeSnapshot[]> {
  return fetchJson(`${API_BASE}/snapshots`);
}

export async function getTerritory(snapshotId: number): Promise<Territory> {
  return fetchJson(`${API_BASE}/territories/${snapshotId}`);
}

export async function getAllTerritories(): Promise<Territory[]> {
  return fetchJson(`${API_BASE}/territories`);
}

export async function getBaseMap(featureType: string = 'land'): Promise<BaseMap> {
  return fetchJson(`${API_BASE}/basemap/${featureType}`);
}
