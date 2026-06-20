import { useState } from 'react';
import { useTechnicalConfig, useTechnicalDetectors } from '../hooks/useTechnicalAnalysis';
import { useNewsList } from '../hooks/useNews';
import { triggerTechnicalAnalysis, updateTechnicalConfig } from '../services/api';
import NewsFilters from '../components/news/NewsFilters';
import NewsTable from '../components/news/NewsTable';
import Pagination from '../components/common/Pagination';
import Loading from '../components/common/Loading';
import ErrorState from '../components/common/ErrorState';

export default function TechnicalPage() {
  const [tab, setTab] = useState<'news' | 'config'>('news');
  const { data: newsData, loading: newsLoading, error: newsError, params, setParams, refresh: refreshNews } = useNewsList({ page: 1, page_size: 20, news_type: 'technical' });
  const { data: config, loading: configLoading, refresh: refreshConfig } = useTechnicalConfig();
  const { data: detectors } = useTechnicalDetectors();
  const [analyzing, setAnalyzing] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      await triggerTechnicalAnalysis();
      await refreshNews();
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSaveConfig = async () => {
    if (!config) return;
    setSaving(true);
    try {
      await updateTechnicalConfig({
        top_n: config.top_n,
        timeframes: config.timeframes,
        min_consecutive: config.min_consecutive,
        rsi_period: config.rsi_period,
        rsi_overbought: config.rsi_overbought,
        rsi_oversold: config.rsi_oversold,
        volume_period: config.volume_period,
        volume_multiplier: config.volume_multiplier,
        min_volume_usdt: config.min_volume_usdt,
        min_price_change_pct: config.min_price_change_pct,
        interval_seconds: config.interval_seconds,
      });
      alert('配置已保存');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">📈 技术面分析</h2>
        <div className="flex gap-2">
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {analyzing ? '分析中...' : '运行技术分析'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b">
        <button
          onClick={() => setTab('news')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            tab === 'news' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          技术快讯
        </button>
        <button
          onClick={() => setTab('config')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            tab === 'config' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          检测配置
        </button>
      </div>

      {tab === 'news' && (
        <>
          <NewsFilters params={params} onChange={setParams} />
          {newsLoading ? (
            <Loading />
          ) : newsError ? (
            <ErrorState message={newsError} onRetry={refreshNews} />
          ) : newsData ? (
            <>
              <div className="text-xs text-gray-400 mb-2">
                共 {newsData.total} 条技术快讯
              </div>
              <NewsTable
                items={newsData.items}
                selectedIds={new Set()}
                onSelect={() => {}}
                onProcess={() => {}}
              />
              <Pagination
                page={newsData.page}
                pageSize={newsData.page_size}
                total={newsData.total}
                onChange={(page) => setParams({ ...params, page })}
              />
            </>
          ) : null}
        </>
      )}

      {tab === 'config' && (
        <div className="grid grid-cols-2 gap-6">
          {/* 检测器列表 */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-gray-900 mb-4">已启用检测器</h3>
            {detectors.length === 0 ? (
              <p className="text-sm text-gray-400">暂无检测器</p>
            ) : (
              <ul className="space-y-2">
                {detectors.map((d) => (
                  <li key={d.name} className="flex items-center gap-2 text-sm">
                    <span className="w-2 h-2 rounded-full bg-green-500" />
                    <span className="font-medium">{d.name}</span>
                    <span className="text-gray-400 text-xs">({d.type})</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* 配置表单 */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-gray-900 mb-4">监控参数</h3>
            {configLoading ? (
              <Loading />
            ) : config ? (
              <div className="space-y-4">
                <ConfigField label="监控币种数量" value={config.top_n} onChange={(v) => { config.top_n = v; refreshConfig(); }} />
                <ConfigField label="时间周期" value={config.timeframes.join(', ')} onChange={() => {}} disabled />
                <ConfigField label="最小连续涨跌" value={config.min_consecutive} onChange={(v) => { config.min_consecutive = v; }} />
                <ConfigField label="RSI 周期" value={config.rsi_period} onChange={(v) => { config.rsi_period = v; }} />
                <ConfigField label="RSI 超买阈值" value={config.rsi_overbought} onChange={(v) => { config.rsi_overbought = v; }} />
                <ConfigField label="RSI 超卖阈值" value={config.rsi_oversold} onChange={(v) => { config.rsi_oversold = v; }} />
                <ConfigField label="成交量周期" value={config.volume_period} onChange={(v) => { config.volume_period = v; }} />
                <ConfigField label="成交量倍数阈值" value={config.volume_multiplier} onChange={(v) => { config.volume_multiplier = v; }} />
                <ConfigField label="最低成交量(USDT)" value={config.min_volume_usdt} onChange={(v) => { config.min_volume_usdt = v; }} />
                <ConfigField label="最低波动率(%)" value={config.min_price_change_pct} onChange={(v) => { config.min_price_change_pct = v; }} />
                <button
                  onClick={handleSaveConfig}
                  disabled={saving}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? '保存中...' : '保存配置'}
                </button>
              </div>
            ) : (
              <p className="text-sm text-gray-400">加载配置失败</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function ConfigField({
  label,
  value,
  onChange,
  disabled,
}: {
  label: string;
  value: number | string;
  onChange: (value: number) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <label className="text-sm text-gray-600">{label}</label>
      <input
        type={typeof value === 'number' ? 'number' : 'text'}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-28 border rounded px-2 py-1 text-sm text-right focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
      />
    </div>
  );
}
