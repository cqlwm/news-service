export function formatTime(iso: string | null | undefined): string {
  if (!iso) return '-';
  const d = new Date(iso);
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待处理',
    generated: '已生成',
    published: '已发布',
    generation_failed: '生成失败',
    publish_failed: '发布失败',
    discarded: '已废弃',
    draft: '草稿',
  };
  return map[status] ?? status;
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    generated: 'bg-blue-100 text-blue-800',
    published: 'bg-green-100 text-green-800',
    generation_failed: 'bg-red-100 text-red-800',
    publish_failed: 'bg-orange-100 text-orange-800',
    discarded: 'bg-gray-200 text-gray-500',
    draft: 'bg-gray-100 text-gray-800',
  };
  return map[status] ?? 'bg-gray-100 text-gray-800';
}
