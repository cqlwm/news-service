import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useNewsDetail } from '../hooks/useNews';
import { generatePost, publishPost, processNews, discardNews } from '../services/api';
import { formatTime, statusLabel, statusColor } from '../utils/format';
import PostCard from '../components/news/PostCard';
import ImageGallery from '../components/news/ImageGallery';
import Loading from '../components/common/Loading';
import ErrorState from '../components/common/ErrorState';

export default function NewsDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, loading, error, refresh } = useNewsDetail(id);
  const [generating, setGenerating] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [discarding, setDiscarding] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;
  if (!data) return <ErrorState message="新闻不存在" />;

  const handleGenerate = async () => {
    setGenerating(true);
    setErrorMsg(null);
    try {
      await generatePost(data.id);
      await refresh();
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : '生成失败');
    } finally {
      setGenerating(false);
    }
  };

  const handlePublish = async () => {
    setPublishing(true);
    setErrorMsg(null);
    try {
      await publishPost(data.id);
      await refresh();
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : '发布失败');
    } finally {
      setPublishing(false);
    }
  };

  const handleProcess = async () => {
    setProcessing(true);
    setErrorMsg(null);
    try {
      await processNews(data.id);
      await refresh();
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : '处理失败');
    } finally {
      setProcessing(false);
    }
  };

  const handleDiscard = async () => {
    if (!window.confirm('确定废弃这条新闻？废弃后不可恢复。')) return;
    setDiscarding(true);
    setErrorMsg(null);
    try {
      await discardNews(data.id);
      await refresh();
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : '废弃失败');
    } finally {
      setDiscarding(false);
    }
  };

  return (
    <div>
      <button onClick={() => navigate('/news')} className="text-sm text-blue-600 hover:underline mb-4 inline-block">
        ← 返回列表
      </button>

      <div className="bg-white rounded-xl border p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 flex-1 mr-4">{data.title}</h2>
          <span className={`shrink-0 px-3 py-1 rounded text-sm font-medium ${statusColor(data.status)}`}>
            {statusLabel(data.status)}
          </span>
        </div>

        <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
          <span>来源: {data.source}</span>
          <span>发布时间: {formatTime(data.published_at)}</span>
          <span>入库时间: {formatTime(data.fetched_at)}</span>
        </div>

        {data.content && (
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap mb-4">
            {data.content}
          </div>
        )}

        <div className="flex gap-2 flex-wrap">
          {data.status === 'pending' && (
            <button onClick={handleProcess} disabled={processing} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
              {processing ? '处理中...' : '处理并发布'}
            </button>
          )}
          {data.status === 'generation_failed' && (
            <button onClick={handleGenerate} disabled={generating} className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50">
              {generating ? '生成中...' : '重新生成贴文'}
            </button>
          )}
          {data.status === 'publish_failed' && (
            <button onClick={handleGenerate} disabled={generating} className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50">
              {generating ? '生成中...' : '重新生成贴文'}
            </button>
          )}
          {(data.status === 'generation_failed' || data.status === 'publish_failed') && (
            <button onClick={handleDiscard} disabled={discarding} className="px-4 py-2 border border-red-300 text-red-600 rounded-lg text-sm hover:bg-red-50 disabled:opacity-50">
              {discarding ? '废弃中...' : '废弃'}
            </button>
          )}
        </div>
        {errorMsg && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
            ⚠️ {errorMsg}
            {errorMsg.includes('LLM') && errorMsg.includes('配置') && (
              <a href="/settings" className="ml-2 text-blue-600 hover:underline font-medium">
                去配置 →
              </a>
            )}
          </div>
        )}
      </div>

      <ImageGallery images={data.images} />

      {data.post && (
        <div className="mt-6">
          <PostCard
            post={data.post}
            newsStatus={data.status}
            onRegenerate={handleGenerate}
            onPublish={handlePublish}
            generating={generating}
            publishing={publishing}
          />
        </div>
      )}
    </div>
  );
}
