import type { FilterInfo } from '../../types';

interface Props {
  filters: FilterInfo[];
  onRemove: (name: string) => void;
}

export default function FilterList({ filters, onRemove }: Props) {
  if (filters.length === 0) {
    return <p className="text-sm text-gray-400 py-4">暂无过滤器，请添加。</p>;
  }
  return (
    <div className="space-y-2">
      {filters.map((f) => (
        <div key={f.name} className="flex items-center justify-between bg-white border rounded-lg px-4 py-3">
          <div>
            <span className="font-medium text-sm text-gray-900">{f.name}</span>
            <span className="ml-2 text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">{f.type}</span>
          </div>
          <button onClick={() => onRemove(f.name)} className="text-red-500 hover:text-red-700 text-sm">
            移除
          </button>
        </div>
      ))}
    </div>
  );
}
