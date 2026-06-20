import { useState, useEffect } from 'react';
import { useScheduler } from '../hooks/useScheduler';
import { fetchSettings, updateSettings, reloadSettings } from '../services/api';
import StatusBadge from '../components/layout/StatusBadge';
import Loading from '../components/common/Loading';

export default function SettingsPage() {
  const { status, loading, start, stop, updateInterval, refresh } = useScheduler();
  const [intervalInput, setIntervalInput] = useState('60');
  const [saving, setSaving] = useState(false);

  // OpenAI 配置
  const [openaiApiKey, setOpenaiApiKey] = useState('');
  const [openaiBaseUrl, setOpenaiBaseUrl] = useState('');
  const [openaiModel, setOpenaiModel] = useState('');
  const [configLoading, setConfigLoading] = useState(true);
  const [configSaving, setConfigSaving] = useState(false);
  const [configMessage, setConfigMessage] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);

  useEffect(() => {
    if (status) setIntervalInput(String(status.interval));
  }, [status]);

  useEffect(() => {
    fetchSettings()
      .then((s) => {
        setOpenaiApiKey(s.openai_api_key || '');
        setOpenaiBaseUrl(s.openai_base_url || '');
        setOpenaiModel(s.openai_model || '');
      })
      .catch(() => {})
      .finally(() => setConfigLoading(false));
  }, []);

  const handleSaveInterval = async () => {
    const val = parseInt(intervalInput, 10);
    if (isNaN(val) || val < 10) return;
    setSaving(true);
    try {
      await updateInterval(val);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveConfig = async () => {
    setConfigSaving(true);
    setConfigMessage('');
    try {
      const payload: Record<string, string> = {};
      if (openaiApiKey) payload.openai_api_key = openaiApiKey;
      if (openaiBaseUrl) payload.openai_base_url = openaiBaseUrl;
      if (openaiModel) payload.openai_model = openaiModel;

      await updateSettings(payload);
      await reloadSettings();
      setConfigMessage('✅ 配置已保存并生效');
    } catch (e) {
      setConfigMessage(`❌ 保存失败: ${e instanceof Error ? e.message : '未知错误'}`);
    } finally {
      setConfigSaving(false);
    }
  };

  if (loading && configLoading) return <Loading />;

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-6">⚙️ 设置</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左列：调度设置 */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-gray-900 mb-4">调度器状态</h3>
            <div className="flex items-center gap-4 mb-4">
              {status && <StatusBadge running={status.running} />}
              {status?.running
                ? <button onClick={stop} className="px-4 py-2 border rounded-lg text-sm text-red-600 hover:bg-red-50">停止</button>
                : <button onClick={start} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">启动</button>
              }
              <button onClick={refresh} className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50">刷新</button>
            </div>
            {status && (
              <div className="text-sm text-gray-500 space-y-1">
                <p>上次运行: {status.last_run ? new Date(status.last_run).toLocaleString('zh-CN') : '暂无'}</p>
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-gray-900 mb-4">采集间隔</h3>
            <div className="flex items-center gap-3">
              <input
                type="number"
                min={10}
                value={intervalInput}
                onChange={(e) => setIntervalInput(e.target.value)}
                className="border rounded-lg px-3 py-2 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-500">秒</span>
              <button onClick={handleSaveInterval} disabled={saving} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>

        {/* 右列：OpenAI 配置 */}
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-semibold text-gray-900 mb-4">🤖 OpenAI 配置</h3>
          <p className="text-sm text-gray-500 mb-4">
            配置 LLM 参数，用于将新闻改写为社交媒体贴文。配置保存在服务端数据库中，修改后自动生效。
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
              <div className="flex gap-2">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={openaiApiKey}
                  onChange={(e) => setOpenaiApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="border rounded-lg px-3 py-2 text-sm flex-1 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                />
                <button
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="px-3 py-2 border rounded-lg text-sm text-gray-500 hover:bg-gray-50"
                >
                  {showApiKey ? '隐藏' : '显示'}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
              <input
                type="text"
                value={openaiBaseUrl}
                onChange={(e) => setOpenaiBaseUrl(e.target.value)}
                placeholder="https://api.openai.com/v1"
                className="border rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
              <input
                type="text"
                value={openaiModel}
                onChange={(e) => setOpenaiModel(e.target.value)}
                placeholder="gpt-4o"
                className="border rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={handleSaveConfig}
              disabled={configSaving}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {configSaving ? '保存中...' : '保存配置'}
            </button>

            {configMessage && (
              <p className={`text-sm ${configMessage.startsWith('✅') ? 'text-green-600' : 'text-red-600'}`}>
                {configMessage}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
