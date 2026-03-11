"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { AgentRunStatus, DepartmentType } from "@/types";
import type { AgentRun } from "@/types";
import { formatDateTime } from "@/lib/utils";
import { CheckCircle2, Clock, Loader2, XCircle } from "lucide-react";

const mockRuns: AgentRun[] = [
  {
    id: "1",
    company_id: "1",
    department_type: DepartmentType.MARKETING,
    status: AgentRunStatus.COMPLETED,
    summary: "Generated 5 social media posts for Q1 campaign. Scheduled across platforms.",
    tokens_used: 4520,
    cost_usd: 0.045,
    started_at: "2026-03-11T08:00:00Z",
    completed_at: "2026-03-11T08:02:30Z",
    error: null,
  },
  {
    id: "2",
    company_id: "1",
    department_type: DepartmentType.SALES,
    status: AgentRunStatus.RUNNING,
    summary: "Analyzing lead pipeline and preparing outreach sequences...",
    tokens_used: 1200,
    cost_usd: 0.012,
    started_at: "2026-03-11T09:15:00Z",
    completed_at: null,
    error: null,
  },
  {
    id: "3",
    company_id: "1",
    department_type: DepartmentType.CUSTOMER_SUPPORT,
    status: AgentRunStatus.COMPLETED,
    summary: "Resolved 12 support tickets. Escalated 2 to human review.",
    tokens_used: 8900,
    cost_usd: 0.089,
    started_at: "2026-03-11T07:30:00Z",
    completed_at: "2026-03-11T07:45:00Z",
    error: null,
  },
  {
    id: "4",
    company_id: "1",
    department_type: DepartmentType.RESEARCH,
    status: AgentRunStatus.FAILED,
    summary: null,
    tokens_used: 350,
    cost_usd: 0.004,
    started_at: "2026-03-11T06:00:00Z",
    completed_at: "2026-03-11T06:00:15Z",
    error: "Rate limit exceeded. Will retry in next cycle.",
  },
  {
    id: "5",
    company_id: "1",
    department_type: DepartmentType.PRODUCT,
    status: AgentRunStatus.COMPLETED,
    summary: "Compiled user feedback report. Identified 3 high-priority feature requests.",
    tokens_used: 3100,
    cost_usd: 0.031,
    started_at: "2026-03-10T22:00:00Z",
    completed_at: "2026-03-10T22:05:00Z",
    error: null,
  },
];

function StatusIcon({ status }: { status: AgentRunStatus }) {
  switch (status) {
    case AgentRunStatus.COMPLETED:
      return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
    case AgentRunStatus.RUNNING:
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
    case AgentRunStatus.FAILED:
      return <XCircle className="h-4 w-4 text-red-500" />;
    default:
      return <Clock className="h-4 w-4 text-muted-foreground" />;
  }
}

export function ActivityLog() {
  return (
    <div className="space-y-3">
      {mockRuns.map((run) => (
        <Card key={run.id} className="hover:border-primary/30 transition-colors">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="mt-0.5">
                <StatusIcon status={run.status} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant="outline" className="capitalize text-xs">
                    {run.department_type.replace("_", " ")}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {formatDateTime(run.started_at)}
                  </span>
                  <span className="text-xs text-muted-foreground ml-auto">
                    ${run.cost_usd.toFixed(3)}
                  </span>
                </div>
                <p className="mt-1 text-sm text-foreground">
                  {run.summary || run.error || "Processing..."}
                </p>
                {run.error && (
                  <p className="mt-1 text-xs text-destructive">{run.error}</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
