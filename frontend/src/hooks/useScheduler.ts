import { useState, useEffect, useCallback } from 'react';
import type { SchedulerStatus } from '../types';
import { fetchSchedulerStatus, startScheduler, stopScheduler, updateSchedulerInterval } from '../services/api';

export function useScheduler() {
  const [status, setStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    fetchSchedulerStatus()
      .then(setStatus)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const start = async () => {
    const res = await startScheduler();
    setStatus((prev) => prev ? { ...prev, running: res.running } : prev);
    return res;
  };

  const stop = async () => {
    const res = await stopScheduler();
    setStatus((prev) => prev ? { ...prev, running: !res.running } : prev);
    return res;
  };

  const updateInterval = async (interval: number) => {
    const res = await updateSchedulerInterval(interval);
    setStatus((prev) => prev ? { ...prev, interval: res.interval } : prev);
    return res;
  };

  return { status, loading, start, stop, updateInterval, refresh: load };
}
