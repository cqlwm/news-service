import { useState, useEffect, useCallback } from 'react';
import type { Stats } from '../types';
import { fetchStats } from '../services/api';

export function useStats() {
  const [data, setData] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    fetchStats()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to fetch stats'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  return { data, loading, error, refresh: load };
}
