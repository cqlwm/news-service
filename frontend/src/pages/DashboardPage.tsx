import { useEffect, useState } from 'react';
import { useStats } from '../hooks/useStats';
import { useScheduler } from '../hooks/useScheduler';
import { useNewsList } from '../hooks/useNews';
import { triggerFetch, triggerTechnicalAnalysis } from '../services/api';
import StatCard from '../components/dashboard/StatCard';
import StatusPieChart from '../components/dashboard/StatusPieChart';
import RecentNews from '../components/dashboard/RecentNews';
import StatusBadge from '../components/layout/StatusBadge';
import Loading from '../components/common/Loading';
import ErrorState from '../components/common/ErrorState';

export default function DashboardPage() {
  const { data: stats, loading: statsLoading, error: statsError, refresh: refreshStats } = useStats();
  const { status: schedulerStatus, start, stop, refresh: refreshScheduler } = useScheduler();
  const { data: newsData, loading: newsLoading, refresh: refreshNews } = useNewsList({ page: 1, page_size: 5 });
  const [fetching, setFetching] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    refreshStats();
    refreshScheduler();
    refreshNews();
  }, []);

  const handleFetch = async () => {
    setFetching(true);
    try {
      await triggerFetch();
      await refreshStats();
      await refreshNews();
    } finally {
      setFetching(false);
    }
  };

  const handleTechnicalAnalysis = async () => {
    setAnalyzing(true);
    try {
      await triggerTechnicalAnalysis();
      await refreshNews();
    } finally {
      setAnalyzing(false);
    }
  };

  if (statsLoading) return <Loading />;
  if (statsError) return <ErrorState message={statsError} onRetry={refreshStats} />;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">📊 仪表盘</h2>
        <div className="flex items-center gap-3">
          {schedulerStatus && <StatusBadge running={schedulerStatus.running} />}
          <button onClick={handleFetch} disabled={fetching} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
            {fetching ? '采集中...' : '手动采集'}
          </button>
          <button onClick={handleTechnicalAnalysis} disabled={analyzing} className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 disabled:opacity-50">
            {analyzing ? '分析中...' : '技术分析'}
          </button>
          {schedulerStatus?.running
            ? <button onClick={stop} className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50">停止调度</button>
            : <button onClick={start} className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50">启动调度</button>
          }
        </div>
      </div>

      {stats && (
        <>
          <div className="grid grid-cols-5 gap-4 mb-6">
            <StatCard label="新闻总数" value={stats.total_news} />
            <StatCard label="待处理" value={stats.news_by_status.pending ?? 0} color="text-yellow-600" />
            <StatCard label="已生成" value={stats.news_by_status.generated ?? 0} color="text-blue-600" />
            <StatCard label="已发布" value={stats.news_by_status.published ?? 0} color="text-green-600" />
            <StatCard label="失败" value={stats.news_by_status.failed ?? 0} color="text-red-600" />
          </div>

          <div className="grid grid-cols-2 gap-6 mb-6">
            <div className="bg-white rounded-xl border p-5">
              <h3 className="font-semibold text-gray-900 mb-4">状态分布</h3>
              <StatusPieChart data={stats.news_by_status} />
            </div>
            <div className="bg-white rounded-xl border p-5">
              <h3 className="font-semibold text-gray-900 mb-4">贴文统计</h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm"><span className="text-gray-500">总贴文数</span><span className="font-medium">{stats.total_posts}</span></div>
                <div className="flex justify-between text-sm"><span className="text-gray-500">已发布</span><span className="font-medium">{stats.published_posts}</span></div>
                <div className="flex justify-between text-sm"><span className="text-gray-500">总图片数</span><span className="font-medium">{stats.total_images}</span></div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* 调度器状态 */}
      {schedulerStatus && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-white rounded-xl border p-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-2">📰 基本面调度</h4>
            <div className="flex items-center gap-2 mb-1">
              <StatusBadge running={schedulerStatus.running} />
              <span className="text-xs text-gray-400">间隔 {schedulerStatus.interval}s</span>
            </div>
            {schedulerStatus.last_run && (
              <p className="text-xs text-gray-400">上次运行: {new Date(schedulerStatus.last_run).toLocaleString('zh-CN')}</p>
            )}
          </div>
          <div className="bg-white rounded-xl border p-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-2">📈 技术面调度</h4>
            <div className="flex items-center gap-2 mb-1">
              <StatusBadge running={schedulerStatus.technical.running} />
              <span className="text-xs text-gray-400">间隔 {schedulerStatus.technical.interval}s</span>
            </div>
            {schedulerStatus.technical.last_run && (
              <p className="text-xs text-gray-400">上次运行: {new Date(schedulerStatus.technical.last_run).toLocaleString('zh-CN')}</p>
            )}
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">📰 最新新闻</h3>
          <a href="/news" className="text-sm text-blue-600 hover:underline">查看更多 →</a>
        </div>
        {newsLoading ? <Loading text="加载新闻中..." /> : newsData && <RecentNews items={newsData.items} />}
      </div>
    </div>
  );
}
