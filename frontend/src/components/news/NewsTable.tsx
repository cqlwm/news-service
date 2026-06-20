
import { Link } from 'react-router-dom';
import type { NewsItem } from '../../types';
import { formatTime, statusLabel, statusColor } from '../../utils/format';
import EmptyState from '../common/EmptyState';

interface Props {
  items: NewsItem[];
  selectedIds: Set<string>;
  onSelect: (ids: Set<string>) => void;
  onProcess: (id: string) => void;
  onRetry?: (id: string) => void;
  onDiscard?: (id: string) => void;
}

export default function NewsTable({ items, selectedIds, onSelect, onProcess, onRetry, onDiscard }: Props) {
  const toggle = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id); else next.add(id);
    onSelect(next);
  };

  const toggleAll = () => {
    if (selectedIds.size === items.length) {
      onSelect(new Set());
    } else {
      onSelect(new Set(items.map((i) => i.id)));
    }
  };

  if (items.length === 0) return <EmptyState title="没有找到新闻" description="尝试调整过滤条件" />;

  return (
    <div className="bg-white rounded-xl border overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-gray-50 text-left text-gray-500">
            <th className="w-10 px-4 py-3">
              <input type="checkbox" checked={selectedIds.size === items.length && items.length > 0} onChange={toggleAll} className="accent-blue-600" />
            </th>
            <th className="px-4 py-3 font-medium">标题</th>
            <th className="w-28 px-4 py-3 font-medium">来源</th>
            <th className="w-24 px-4 py-3 font-medium">状态</th>
            <th className="w-36 px-4 py-3 font-medium">时间</th>
            <th className="w-28 px-4 py-3 font-medium">操作</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-b last:border-0 hover:bg-gray-50">
              <td className="px-4 py-3">
                <input type="checkbox" checked={selectedIds.has(item.id)} onChange={() => toggle(item.id)} className="accent-blue-600" />
              </td>
              <td className="px-4 py-3">
                <Link to={`/news/${item.id}`} className="text-blue-600 hover:underline font-medium">
                  {item.title}
                </Link>
              </td>
              <td className="px-4 py-3 text-gray-500">{item.source}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColor(item.status)}`}>
                  {statusLabel(item.status)}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-400 text-xs">{formatTime(item.published_at)}</td>
              <td className="px-4 py-3">
                {item.status === 'pending' && (
                  <button onClick={() => onProcess(item.id)} className="text-blue-600 hover:underline text-xs">
                    处理
                  </button>
                )}
                {item.status === 'generation_failed' && onRetry && (
                  <button onClick={() => onRetry(item.id)} className="text-blue-600 hover:underline text-xs mr-2">
                    重试
                  </button>
                )}
                {item.status === 'publish_failed' && onRetry && (
                  <button onClick={() => onRetry(item.id)} className="text-blue-600 hover:underline text-xs mr-2">
                    重试
                  </button>
                )}
                {(item.status === 'generation_failed' || item.status === 'publish_failed') && onDiscard && (
                  <button onClick={() => onDiscard(item.id)} className="text-red-500 hover:underline text-xs">
                    废弃
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
