interface Props {
  title?: string;
  description?: string;
}

export default function EmptyState({ title = '暂无数据', description }: Props) {
  return (
    <div className="text-center py-12 text-gray-400">
      <div className="text-5xl mb-4">📭</div>
      <p className="text-lg font-medium">{title}</p>
      {description && <p className="text-sm mt-1">{description}</p>}
    </div>
  );
}
