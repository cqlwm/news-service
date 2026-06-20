import { useState } from 'react';
import type { NewsQueryParams } from '../../types';

interface Props {
  params: NewsQueryParams;
  onChange: (params: NewsQueryParams) => void;
}

export default function NewsFilters({ params, onChange }: Props) {
  const [keyword, setKeyword] = useState(params.keyword || '');
  const [status, setStatus] = useState(params.status || '');
  const [source, setSource] = useState(params.source || '');
  const [newsType, setNewsType] = useState(params.news_type || '');

  const apply = () => {
    onChange({
      ...params,
      keyword: keyword || undefined,
      status: status || undefined,
      source: source || undefined,
      news_type: newsType || undefined,
      page: 1,
    });
  };

  const reset = () => {
    setKeyword('');
    setStatus('');
    setSource('');
    setNewsType('');
    onChange({ page: 1, page_size: 20 });
  };

  return (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      <input
        type="text"
        placeholder="搜索标题/内容..."
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && apply()}
        className="border rounded-lg px-3 py-2 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <select
        value={status}
        onChange={(e) => setStatus(e.target.value)}
        className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">全部状态</option>
        <option value="pending">待处理</option>
        <option value="generated">已生成</option>
        <option value="published">已发布</option>
        <option value="generation_failed">生成失败</option>
        <option value="publish_failed">发布失败</option>
        <option value="discarded">已废弃</option>
      </select>
      <select
        value={newsType}
        onChange={(e) => setNewsType(e.target.value)}
        className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">全部类型</option>
        <option value="fundamental">基本面</option>
        <option value="technical">技术面</option>
      </select>
      <input
        type="text"
        placeholder="来源过滤..."
        value={source}
        onChange={(e) => setSource(e.target.value)}
        className="border rounded-lg px-3 py-2 text-sm w-40 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button onClick={apply} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
        搜索
      </button>
      <button onClick={reset} className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50">
        重置
      </button>
    </div>
  );
}
