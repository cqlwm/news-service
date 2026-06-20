export interface NewsItem {
  id: string;
  title: string;
  content: string | null;
  source: string;
  url: string;
  published_at: string | null;
  fetched_at: string;
  status: NewsStatus;
  created_at: string;
  type?: string;
  pattern_type?: string;
}

export type NewsStatus = 'pending' | 'generated' | 'published' | 'generation_failed' | 'publish_failed' | 'discarded';

export interface NewsImage {
  id: number;
  news_id: string;
  image_url: string;
  local_path: string;
  downloaded_at: string;
}

export interface Post {
  id: number;
  news_id: string;
  base_asset: string;
  content: string;
  status: 'draft' | 'published';
  published_at: string | null;
  created_at: string;
}

export interface NewsDetail extends NewsItem {
  images: NewsImage[];
  post: Post | null;
}

export interface NewsListResponse {
  items: NewsItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface Stats {
  total_news: number;
  news_by_status: Record<string, number>;
  total_images: number;
  total_posts: number;
  published_posts: number;
}

export interface TechnicalSchedulerInfo {
  running: boolean;
  interval: number;
  last_run: string | null;
}

export interface SchedulerStatus {
  running: boolean;
  interval: number;
  last_run: string | null;
  technical: TechnicalSchedulerInfo;
}

export interface FilterInfo {
  name: string;
  type: string;
}

export interface NewsQueryParams {
  page?: number;
  page_size?: number;
  status?: string;
  keyword?: string;
  source?: string;
  date_from?: string;
  date_to?: string;
  news_type?: string;
}

export interface AppSettings {
  openai_api_key?: string;
  openai_base_url?: string;
  openai_model?: string;
  fetch_interval?: string;
  max_news_per_fetch?: string;
  [key: string]: string | undefined;
}

export interface TechnicalConfig {
  top_n: number;
  timeframes: string[];
  min_consecutive: number;
  rsi_period: number;
  rsi_overbought: number;
  rsi_oversold: number;
  volume_period: number;
  volume_multiplier: number;
  min_volume_usdt: number;
  min_price_change_pct: number;
  interval_seconds: number;
}

export interface DetectorInfo {
  name: string;
  type: string;
}
