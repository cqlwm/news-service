import { useState, useEffect, useCallback } from 'react';
import type { NewsListResponse, NewsDetail, NewsQueryParams } from '../types';
import { fetchNewsList, fetchNewsDetail, deleteNews } from '../services/api';

export function useNewsList(initialParams: NewsQueryParams = {}) {
  const [data, setData] = useState<NewsListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useState<NewsQueryParams>({ page: 1, page_size: 20, ...initialParams });

  const load = useCallback(async (p: NewsQueryParams) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchNewsList(p);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch news');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(params); }, [params, load]);

  return {
    data,
    loading,
    error,
    params,
    setParams,
    refresh: () => load(params),
  };
}

export function useNewsDetail(id: string | undefined) {
  const [data, setData] = useState<NewsDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetchNewsDetail(id)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to fetch detail'))
      .finally(() => setLoading(false));
  }, [id]);

  return { data, loading, error, refresh: () => id && fetchNewsDetail(id).then(setData) };
}

export function useDeleteNews() {
  const [loading, setLoading] = useState(false);
  const remove = async (id: string) => {
    setLoading(true);
    await deleteNews(id);
    setLoading(false);
  };
  return { remove, loading };
}
