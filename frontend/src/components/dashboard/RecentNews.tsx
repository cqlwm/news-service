import { Link } from 'react-router-dom';
import type { NewsItem } from '../../types';
import { formatTime, statusLabel, statusColor } from '../../utils/format';

interface Props {
  items: NewsItem[];
}

export default function RecentNews({ items }: Props) {
  return (
    <div className="space-y-2">
      {items.map((item) => (
        <Link
          key={item.id}
          to={`/news/${item.id}`}
          className="block p-3 rounded-lg border hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-start justify-between gap-3">
            <p className="text-sm font-medium text-gray-900 truncate flex-1">{item.title}</p>
            <span className={`shrink-0 px-2 py-0.5 rounded text-xs font-medium ${statusColor(item.status)}`}>
              {statusLabel(item.status)}
            </span>
          </div>
          <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
            <span>{item.source}</span>
            <span>{formatTime(item.published_at)}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}
