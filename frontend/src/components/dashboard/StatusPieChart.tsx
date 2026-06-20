import { statusLabel } from '../../utils/format';

interface Props {
  data: Record<string, number>;
}

const COLORS: Record<string, string> = {
  pending: '#eab308',
  generated: '#3b82f6',
  published: '#22c55e',
  failed: '#ef4444',
};

export default function StatusPieChart({ data }: Props) {
  const entries = Object.entries(data);
  const total = entries.reduce((s, [, v]) => s + v, 0);
  if (total === 0) return <div className="text-gray-400 text-sm text-center py-8">暂无数据</div>;

  let cumulative = 0;

  return (
    <div className="flex items-center gap-6">
      <svg width="140" height="140" viewBox="0 0 32 32">
        {entries.map(([key, value]) => {
          const pct = value / total;
          const startAngle = cumulative * 360;
          cumulative += pct;
          const endAngle = cumulative * 360;
          const x1 = 16 + 14 * Math.cos((startAngle * Math.PI) / 180);
          const y1 = 16 + 14 * Math.sin((startAngle * Math.PI) / 180);
          const x2 = 16 + 14 * Math.cos((endAngle * Math.PI) / 180);
          const y2 = 16 + 14 * Math.sin((endAngle * Math.PI) / 180);
          const largeArc = pct > 0.5 ? 1 : 0;
          return (
            <path
              key={key}
              d={`M 16 16 L ${x1} ${y1} A 14 14 0 ${largeArc} 1 ${x2} ${y2} Z`}
              fill={COLORS[key] || '#9ca3af'}
            />
          );
        })}
      </svg>
      <div className="space-y-1.5">
        {entries.map(([key, value]) => (
          <div key={key} className="flex items-center gap-2 text-sm">
            <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: COLORS[key] || '#9ca3af' }} />
            <span className="text-gray-600">{statusLabel(key)}</span>
            <span className="font-medium">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
