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

export interface SchedulerStatus {
  running: boolean;
  interval: number;
  last_run: string | null;
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
}

export interface AppSettings {
  openai_api_key?: string;
  openai_base_url?: string;
  openai_model?: string;
  fetch_interval?: string;
  max_news_per_fetch?: string;
  [key: string]: string | undefined;
}
