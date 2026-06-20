import { useState, useEffect } from 'react';
import { useScheduler } from '../hooks/useScheduler';
import { fetchSettings, updateSettings, reloadSettings } from '../services/api';
import StatusBadge from '../components/layout/StatusBadge';
import Loading from '../components/common/Loading';

const DEFAULT_SYSTEM_PROMPT = '你是一个专业的加密货币新闻编辑，擅长将新闻改写为社交媒体贴文。';

const DEFAULT_USER_TEMPLATE = `请将以下新闻改写为适合社交媒体发布的贴文格式：

要求：
1. 简洁有力，吸引眼球
2. 在开头明确指出主要涉及的加密货币（格式：$BTC $ETH 等），如果有多个最多3个
3. 长度控制在200字以内
4. 语气专业但不失活泼
5. 可以适当的添加一些emoji让内容更生动

新闻标题：{title}
新闻内容：{content}

请按以下格式返回：
BASE_ASSET: BTC
CONTENT: 这里是贴文内容...`;

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

  // 提示词配置
  const [promptSystem, setPromptSystem] = useState('');
  const [promptUserTemplate, setPromptUserTemplate] = useState('');
  const [promptSaving, setPromptSaving] = useState(false);
  const [promptMessage, setPromptMessage] = useState('');

  useEffect(() => {
    if (status) setIntervalInput(String(status.interval));
  }, [status]);

  useEffect(() => {
    fetchSettings()
      .then((s) => {
        setOpenaiApiKey(s.openai_api_key || '');
        setOpenaiBaseUrl(s.openai_base_url || '');
        setOpenaiModel(s.openai_model || '');
        setPromptSystem(s.prompt_system || '');
        setPromptUserTemplate(s.prompt_user_template || '');
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

  const handleSavePrompts = async () => {
    setPromptSaving(true);
    setPromptMessage('');
    try {
      const payload: Record<string, string> = {};
      if (promptSystem) payload.prompt_system = promptSystem;
      if (promptUserTemplate) payload.prompt_user_template = promptUserTemplate;

      await updateSettings(payload);
      await reloadSettings();
      setPromptMessage('✅ 提示词已保存并生效');
    } catch (e) {
      setPromptMessage(`❌ 保存失败: ${e instanceof Error ? e.message : '未知错误'}`);
    } finally {
      setPromptSaving(false);
    }
  };

  const handleResetPrompts = async () => {
    setPromptSystem(DEFAULT_SYSTEM_PROMPT);
    setPromptUserTemplate(DEFAULT_USER_TEMPLATE);
    setPromptSaving(true);
    setPromptMessage('');
    try {
      await updateSettings({
        prompt_system: DEFAULT_SYSTEM_PROMPT,
        prompt_user_template: DEFAULT_USER_TEMPLATE,
      });
      await reloadSettings();
      setPromptMessage('✅ 已重置为默认提示词');
    } catch (e) {
      setPromptMessage(`❌ 重置失败: ${e instanceof Error ? e.message : '未知错误'}`);
    } finally {
      setPromptSaving(false);
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

      {/* 提示词模板区域 - 全宽 */}
      <div className="mt-6 bg-white rounded-xl border p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">📝 提示词模板</h3>
          <button
            onClick={handleResetPrompts}
            disabled={promptSaving}
            className="px-3 py-1.5 border rounded-lg text-sm text-gray-500 hover:bg-gray-50 disabled:opacity-50"
          >
            重置为默认
          </button>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          自定义 LLM 提示词模板。用户模板中使用 <code className="bg-gray-100 px-1 rounded text-xs">{'{title}'}</code> 和 <code className="bg-gray-100 px-1 rounded text-xs">{'{content}'}</code> 作为新闻标题和内容的占位符。
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">System Prompt</label>
            <textarea
              value={promptSystem}
              onChange={(e) => setPromptSystem(e.target.value)}
              rows={4}
              className="border rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono resize-y"
              placeholder={DEFAULT_SYSTEM_PROMPT}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">User Template</label>
            <textarea
              value={promptUserTemplate}
              onChange={(e) => setPromptUserTemplate(e.target.value)}
              rows={12}
              className="border rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono resize-y"
              placeholder={DEFAULT_USER_TEMPLATE}
            />
          </div>
        </div>

        <div className="flex items-center gap-3 mt-4">
          <button
            onClick={handleSavePrompts}
            disabled={promptSaving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {promptSaving ? '保存中...' : '保存提示词'}
          </button>
          {promptMessage && (
            <p className={`text-sm ${promptMessage.startsWith('✅') ? 'text-green-600' : 'text-red-600'}`}>
              {promptMessage}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
