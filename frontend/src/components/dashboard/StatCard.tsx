interface Props {
  label: string;
  value: number;
  color?: string;
}

export default function StatCard({ label, value, color = 'text-gray-900' }: Props) {
  return (
    <div className="bg-white rounded-xl border p-5">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value.toLocaleString()}</p>
    </div>
  );
}
