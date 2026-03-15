"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getSchedulerStatus, startScheduler, stopScheduler } from "@/lib/api";

interface CronJob {
  department?: string;
  name?: string;
  schedule?: string;
  next_run?: string;
  last_run_status?: string;
  [key: string]: unknown;
}

interface SchedulerControlsProps {
  companyId: string;
}

export function SchedulerControls({ companyId }: SchedulerControlsProps) {
  const [jobs, setJobs] = useState<CronJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);

  const isRunning = jobs.length > 0;

  useEffect(() => {
    loadStatus();
  }, [companyId]);

  async function loadStatus() {
    setLoading(true);
    const res = await getSchedulerStatus(companyId);
    if (res.data) {
      setJobs((res.data.jobs || []) as CronJob[]);
    }
    setLoading(false);
  }

  async function handleToggle() {
    setToggling(true);
    if (isRunning) {
      await stopScheduler(companyId);
    } else {
      await startScheduler(companyId);
    }
    await loadStatus();
    setToggling(false);
  }

  function formatNextRun(dateStr: string | undefined): string {
    if (!dateStr) return "—";
    const d = new Date(dateStr);
    return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
  }

  return (
    <Card className="p-4 bg-gray-900 border-gray-800">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-white">Scheduler</h3>
          <div className="flex items-center gap-1.5">
            <span
              className={`inline-block w-2 h-2 rounded-full ${
                isRunning ? "bg-green-500" : "bg-gray-600"
              }`}
            />
            <span className="text-xs text-gray-500">{isRunning ? "Running" : "Stopped"}</span>
          </div>
        </div>
        <Button
          size="sm"
          variant={isRunning ? "destructive" : "default"}
          disabled={loading || toggling}
          onClick={handleToggle}
          className="text-xs h-7"
        >
          {toggling ? "..." : isRunning ? "Stop" : "Start"}
        </Button>
      </div>

      {loading ? (
        <p className="text-gray-600 text-xs">Loading...</p>
      ) : jobs.length === 0 ? (
        <p className="text-gray-600 text-xs">No cron jobs registered</p>
      ) : (
        <div className="space-y-2">
          {jobs.map((job, i) => (
            <div
              key={i}
              className="flex items-center justify-between text-xs py-1.5 border-t border-gray-800 first:border-0"
            >
              <div className="flex items-center gap-2">
                <span className="text-gray-300 capitalize">{job.department || job.name || "Job"}</span>
                {job.schedule && (
                  <span className="text-gray-600 font-mono">{job.schedule}</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {job.next_run && (
                  <span className="text-gray-500">Next: {formatNextRun(job.next_run)}</span>
                )}
                {job.last_run_status && (
                  <Badge
                    variant={job.last_run_status === "completed" ? "success" : job.last_run_status === "failed" ? "destructive" : "secondary"}
                    className="text-[10px] px-1.5 py-0"
                  >
                    {job.last_run_status}
                  </Badge>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
