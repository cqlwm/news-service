import type { Post } from '../../types';
import { formatTime } from '../../utils/format';

interface Props {
  post: Post;
  newsStatus?: string;
  onRegenerate?: () => void;
  onPublish?: () => void;
  generating?: boolean;
  publishing?: boolean;
}

export default function PostCard({ post, newsStatus, onRegenerate, onPublish, generating, publishing }: Props) {
  return (
    <div className="bg-white rounded-xl border p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900">生成的贴文</h3>
        <span className="text-xs text-gray-400">Base Asset: {post.base_asset}</span>
      </div>
      <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
        {post.content}
      </div>
      <div className="flex items-center justify-between mt-3">
        <span className="text-xs text-gray-400">
          {post.status === 'published' ? `已发布 ${formatTime(post.published_at)}` : '草稿'}
        </span>
        <div className="flex gap-2">
          {onRegenerate && newsStatus && newsStatus !== 'published' && newsStatus !== 'discarded' && (
            <button onClick={onRegenerate} disabled={generating} className="px-3 py-1.5 border rounded text-sm hover:bg-gray-50 disabled:opacity-50">
              {generating ? '生成中...' : '重新生成'}
            </button>
          )}
          {onPublish && post.status === 'draft' && newsStatus && newsStatus !== 'published' && newsStatus !== 'discarded' && (
            <button onClick={onPublish} disabled={publishing} className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50">
              {publishing ? '发布中...' : '发布'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
