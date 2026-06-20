import { useState } from 'react';
import { useNewsList } from '../hooks/useNews';
import { processNews, processPendingNews, retryNews, discardNews } from '../services/api';
import NewsFilters from '../components/news/NewsFilters';
import NewsTable from '../components/news/NewsTable';
import Pagination from '../components/common/Pagination';
import Loading from '../components/common/Loading';
import ErrorState from '../components/common/ErrorState';

export default function NewsListPage() {
  const { data, loading, error, params, setParams, refresh } = useNewsList();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [processing, setProcessing] = useState(false);

  const handleProcess = async (id: string) => {
    setProcessing(true);
    try {
      await processNews(id);
      await refresh();
    } finally {
      setProcessing(false);
    }
  };

  const handleBatchProcess = async () => {
    setProcessing(true);
    try {
      await processPendingNews(selectedIds.size || 5);
      setSelectedIds(new Set());
      await refresh();
    } finally {
      setProcessing(false);
    }
  };

  const handleRetry = async (id: string) => {
    try {
      await retryNews(id);
      await refresh();
    } catch (e) {
      alert(e instanceof Error ? e.message : '重试失败');
    }
  };

  const handleDiscard = async (id: string) => {
    if (!window.confirm('确定废弃这条新闻？废弃后不可恢复。')) return;
    try {
      await discardNews(id);
      await refresh();
    } catch (e) {
      alert(e instanceof Error ? e.message : '废弃失败');
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">📰 新闻列表</h2>
        <div className="flex gap-2">
          {selectedIds.size > 0 && (
            <button onClick={handleBatchProcess} disabled={processing} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
              {processing ? '处理中...' : `批量处理 (${selectedIds.size})`}
            </button>
          )}
          <button onClick={refresh} className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            刷新
          </button>
        </div>
      </div>

      <NewsFilters params={params} onChange={setParams} />

      {data && (
        <>
          <div className="text-xs text-gray-400 mb-2">
            共 {data.total} 条，第 {data.page}/{Math.ceil(data.total / data.page_size)} 页
          </div>
          <NewsTable
            items={data.items}
            selectedIds={selectedIds}
            onSelect={setSelectedIds}
            onProcess={handleProcess}
            onRetry={handleRetry}
            onDiscard={handleDiscard}
          />
          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onChange={(page) => setParams({ ...params, page })}
          />
        </>
      )}
    </div>
  );
}
