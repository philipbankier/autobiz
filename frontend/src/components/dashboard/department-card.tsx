"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { smartTrigger } from "@/lib/api";

const deptIcons: Record<string, string> = {
  ceo: "👔", developer: "💻", marketing: "📢",
  sales: "💰", finance: "📊", support: "🎧",
};

interface DepartmentCardProps {
  companyId: string;
  department: {
    type: string;
    status: string;
    autonomy?: string;
    budget_cap_daily?: string | null;
    cost_today?: number;
    last_run_at?: string | null;
    last_run_status?: string | null;
    current_task?: string | null;
  };
}

export function DepartmentCard({ companyId, department }: DepartmentCardProps) {
  const [triggering, setTriggering] = useState(false);
  const [status, setStatus] = useState(department.status);

  const budgetCap = parseFloat(department.budget_cap_daily || "0");
  const spent = department.cost_today || 0;
  const budgetPct = budgetCap > 0 ? Math.min((spent / budgetCap) * 100, 100) : 0;
  const budgetColor = budgetPct > 80 ? "bg-red-500" : budgetPct > 50 ? "bg-yellow-500" : "bg-green-500";

  const isRunning = status === "running";

  async function handleTrigger() {
    setTriggering(true);
    setStatus("running");
    try {
      await smartTrigger(companyId, department.type);
    } finally {
      setTriggering(false);
      // Status will update via SSE or next refresh
    }
  }

  function timeAgo(dateStr: string | null | undefined): string {
    if (!dateStr) return "Never";
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  }

  const statusBadgeVariant = isRunning ? "success" : status === "paused" ? "warning" : "secondary";

  return (
    <Card
      className={`p-4 bg-gray-900 border-gray-800 transition-all ${
        isRunning ? "border-indigo-500/50 shadow-indigo-500/10 shadow-lg animate-pulse-subtle" : ""
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{deptIcons[department.type] || "🏢"}</span>
          <span className="text-white font-semibold capitalize">{department.type}</span>
        </div>
        <Badge variant={statusBadgeVariant}>{status}</Badge>
      </div>

      {/* Budget bar */}
      {budgetCap > 0 && (
        <div className="mb-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Budget</span>
            <span>${spent.toFixed(2)} / ${budgetCap.toFixed(2)}</span>
          </div>
          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${budgetColor}`}
              style={{ width: `${budgetPct}%` }}
            />
          </div>
        </div>
      )}

      {/* Current task */}
      {department.current_task && (
        <p className="text-gray-400 text-xs mb-3 truncate" title={department.current_task}>
          {department.current_task}
        </p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between">
        <div className="text-xs text-gray-500">
          {department.last_run_at ? (
            <span className="flex items-center gap-1">
              {department.last_run_status === "completed" ? "✓" : department.last_run_status === "failed" ? "✗" : "●"}
              {" "}{timeAgo(department.last_run_at)}
            </span>
          ) : (
            <span>No runs yet</span>
          )}
        </div>
        <Button
          size="sm"
          variant={isRunning ? "secondary" : "default"}
          disabled={triggering || isRunning}
          onClick={handleTrigger}
          className="text-xs h-7 px-3"
        >
          {triggering ? "..." : isRunning ? "Running" : "▶ Run"}
        </Button>
      </div>
    </Card>
  );
}
