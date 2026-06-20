import { useState, useEffect, useCallback } from 'react';
import type { TechnicalConfig, DetectorInfo } from '../types';
import { fetchTechnicalConfig, fetchTechnicalDetectors } from '../services/api';

export function useTechnicalConfig() {
  const [data, setData] = useState<TechnicalConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    fetchTechnicalConfig()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to fetch config'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  return { data, loading, error, refresh: load };
}

export function useTechnicalDetectors() {
  const [data, setData] = useState<DetectorInfo[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    fetchTechnicalDetectors()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  return { data, loading, refresh: load };
}
