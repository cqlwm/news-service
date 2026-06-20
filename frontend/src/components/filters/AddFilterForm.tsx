import { useState } from 'react';

interface Props {
  onAdd: (filterType: string, config: Record<string, unknown>) => Promise<void>;
}

export default function AddFilterForm({ onAdd }: Props) {
  const [keywords, setKeywords] = useState('');
  const [matchSource, setMatchSource] = useState(true);
  const [adding, setAdding] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keywords.trim()) return;
    setAdding(true);
    try {
      await onAdd('keyword', {
        keywords: keywords.split(',').map((k) => k.trim()).filter(Boolean),
        match_source: matchSource,
      });
      setKeywords('');
    } finally {
      setAdding(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white border rounded-xl p-5 space-y-4">
      <h3 className="font-semibold text-gray-900">添加过滤器</h3>
      <div>
        <label className="block text-sm text-gray-600 mb-1">类型</label>
        <input type="text" value="keyword" disabled className="border rounded-lg px-3 py-2 text-sm bg-gray-50 w-full" />
      </div>
      <div>
        <label className="block text-sm text-gray-600 mb-1">关键词（逗号分隔）</label>
        <input
          type="text"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          placeholder="BTC, ETH, SOL"
          className="border rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <label className="flex items-center gap-2 text-sm text-gray-600">
        <input type="checkbox" checked={matchSource} onChange={(e) => setMatchSource(e.target.checked)} className="accent-blue-600" />
        匹配来源
      </label>
      <button type="submit" disabled={adding || !keywords.trim()} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
        {adding ? '添加中...' : '添加'}
      </button>
    </form>
  );
}
