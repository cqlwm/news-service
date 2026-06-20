import type {
  NewsListResponse,
  NewsDetail,
  Stats,
  SchedulerStatus,
  FilterInfo,
  NewsQueryParams,
  TechnicalConfig,
  DetectorInfo,
} from '../types';

const BASE = '';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`HTTP ${res.status}: ${body}`);
  }
  return res.json();
}

// ── System ──

export function fetchHealth(): Promise<Record<string, string>> {
  return request('/health');
}

export function fetchStats(): Promise<Stats> {
  return request('/stats');
}

// ── News ──

export function fetchNewsList(params: NewsQueryParams): Promise<NewsListResponse> {
  const qs = new URLSearchParams();
  if (params.page) qs.set('page', String(params.page));
  if (params.page_size) qs.set('page_size', String(params.page_size));
  if (params.status) qs.set('status', params.status);
  if (params.keyword) qs.set('keyword', params.keyword);
  if (params.source) qs.set('source', params.source);
  if (params.date_from) qs.set('date_from', params.date_from);
  if (params.date_to) qs.set('date_to', params.date_to);
  if (params.news_type) qs.set('news_type', params.news_type);
  return request(`/api/news?${qs.toString()}`);
}

export function fetchNewsDetail(id: string): Promise<NewsDetail> {
  return request(`/api/news/${id}`);
}

export function deleteNews(id: string): Promise<{ message: string }> {
  return request(`/api/news/${id}`, { method: 'DELETE' });
}

// ── Pipeline ──

export function triggerFetch(): Promise<{ message: string; new_news_ids: string[] }> {
  return request('/api/pipeline/fetch', { method: 'POST' });
}

export function processNews(id: string): Promise<{ message: string; news_id: string; published: boolean }> {
  return request(`/api/pipeline/process/${id}`, { method: 'POST' });
}

export function processPendingNews(limit = 5): Promise<{ message: string; results: Record<string, boolean> }> {
  return request(`/api/pipeline/process-pending?limit=${limit}`, { method: 'POST' });
}

export function generatePost(newsId: string): Promise<{ message: string; news_id: string; base_asset: string; content: string }> {
  return request(`/api/pipeline/news/${newsId}/generate`, { method: 'POST' });
}

export function publishPost(newsId: string): Promise<{ message: string; news_id: string }> {
  return request(`/api/pipeline/news/${newsId}/publish`, { method: 'POST' });
}

// ── Filters ──

export function fetchFilters(): Promise<FilterInfo[]> {
  return request('/api/filters');
}

export function addFilter(filterType: string, config: Record<string, unknown>): Promise<{ message: string }> {
  return request(`/api/filters?filter_type=${filterType}`, {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

export function removeFilter(name: string): Promise<{ message: string }> {
  return request(`/api/filters/${name}`, { method: 'DELETE' });
}

// ── Scheduler ──

export function startScheduler(): Promise<{ message: string; running: boolean }> {
  return request('/api/scheduler/start', { method: 'POST' });
}

export function stopScheduler(): Promise<{ message: string; running: boolean }> {
  return request('/api/scheduler/stop', { method: 'POST' });
}

export function fetchSchedulerStatus(): Promise<SchedulerStatus> {
  return request('/api/scheduler/status');
}

export function updateSchedulerInterval(interval: number): Promise<{ message: string; interval: number }> {
  return request(`/api/scheduler/interval?interval=${interval}`, { method: 'PUT' });
}

// ── Settings ──

export function fetchSettings(): Promise<Record<string, string>> {
  return request('/api/settings');
}

export function updateSettings(settings: Record<string, string>): Promise<{ message: string; updated: string[] }> {
  return request('/api/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  });
}

export function reloadSettings(): Promise<{ message: string }> {
  return request('/api/settings/reload', { method: 'POST' });
}

export function retryNews(newsId: string): Promise<{ message: string; news_id: string; published: boolean }> {
  return request(`/api/pipeline/news/${newsId}/retry`, { method: 'POST' });
}

export function discardNews(newsId: string): Promise<{ message: string; news_id: string }> {
  return request(`/api/pipeline/news/${newsId}/discard`, { method: 'POST' });
}

// ── Technical Analysis ──

export function triggerTechnicalAnalysis(): Promise<{ message: string; new_ids: string[] }> {
  return request('/api/technical/run', { method: 'POST' });
}

export function fetchTechnicalConfig(): Promise<TechnicalConfig> {
  return request('/api/technical/config');
}

export function updateTechnicalConfig(config: Partial<TechnicalConfig>): Promise<{ message: string; config: Partial<TechnicalConfig> }> {
  return request('/api/technical/config', {
    method: 'PUT',
    body: JSON.stringify(config),
  });
}

export function fetchTechnicalDetectors(): Promise<DetectorInfo[]> {
  return request('/api/technical/detectors');
}
