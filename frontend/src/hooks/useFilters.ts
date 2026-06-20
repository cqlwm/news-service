import { useState, useEffect, useCallback } from 'react';
import type { FilterInfo } from '../types';
import { fetchFilters, addFilter, removeFilter } from '../services/api';

export function useFilters() {
  const [filters, setFilters] = useState<FilterInfo[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    fetchFilters()
      .then(setFilters)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const add = async (filterType: string, config: Record<string, unknown>) => {
    await addFilter(filterType, config);
    await load();
  };

  const remove = async (name: string) => {
    await removeFilter(name);
    await load();
  };

  return { filters, loading, add, remove, refresh: load };
}
