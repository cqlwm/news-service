interface Props {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
}

export default function Pagination({ page, pageSize, total, onChange }: Props) {
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;

  const pages: number[] = [];
  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, page + 2);
  for (let i = start; i <= end; i++) pages.push(i);

  return (
    <div className="flex items-center justify-center gap-2 mt-6">
      <button
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
        className="px-3 py-1.5 rounded border text-sm disabled:opacity-40 hover:bg-gray-50"
      >
        ← 上一页
      </button>
      {start > 1 && <span className="text-gray-400">...</span>}
      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onChange(p)}
          className={`px-3 py-1.5 rounded text-sm font-medium ${
            p === page ? 'bg-blue-600 text-white' : 'border hover:bg-gray-50'
          }`}
        >
          {p}
        </button>
      ))}
      {end < totalPages && <span className="text-gray-400">...</span>}
      <button
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
        className="px-3 py-1.5 rounded border text-sm disabled:opacity-40 hover:bg-gray-50"
      >
        下一页 →
      </button>
    </div>
  );
}
