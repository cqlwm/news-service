import StatusBadge from './StatusBadge';
import type { SchedulerStatus } from '../../types';

interface Props {
  schedulerStatus: SchedulerStatus | null;
}

export default function Header({ schedulerStatus }: Props) {
  return (
    <header className="h-14 bg-white border-b flex items-center justify-between px-6">
      <div className="text-sm text-gray-500">
        新闻采集与发布管理系统
      </div>
      <div className="flex items-center gap-4">
        {schedulerStatus && (
          <div className="flex items-center gap-3 text-sm text-gray-600">
            <StatusBadge running={schedulerStatus.running} />
            <span>间隔: {schedulerStatus.interval}s</span>
          </div>
        )}
      </div>
    </header>
  );
}
