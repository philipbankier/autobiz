"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getActivity, type AgentRun } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const statusColors: Record<string, string> = {
  pending: "bg-yellow-600", running: "bg-blue-600", completed: "bg-green-600", failed: "bg-red-600",
};
const deptIcons: Record<string, string> = {
  ceo: "👔", developer: "💻", marketing: "📢", sales: "💰", finance: "📊", support: "🎧",
};

export default function ActivityPage() {
  const params = useParams();
  const companyId = params.companyId as string;
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getActivity(companyId).then((res) => {
      if (res.data) setRuns(res.data);
      setLoading(false);
    });
  }, [companyId]);

  if (loading) return <p className="text-gray-400">Loading activity...</p>;

  return (
    <div>
      <h2 className="text-lg font-semibold text-white mb-4">Agent Activity</h2>

      {runs.length === 0 ? (
        <Card className="p-8 bg-gray-900 border-gray-800 text-center">
          <p className="text-gray-500">No agent runs yet. Activity will appear here once agents start working.</p>
        </Card>
      ) : (
        <div className="space-y-2">
          {runs.map((run) => (
            <Card key={run.id} className="p-4 bg-gray-900 border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-lg">{deptIcons[run.trigger] || "🤖"}</span>
                <div>
                  <p className="text-white text-sm">{run.summary || `${run.trigger} run`}</p>
                  <p className="text-gray-500 text-xs">
                    {new Date(run.started_at).toLocaleString()}
                    {run.completed_at && ` · ${Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s`}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-gray-400 text-xs">{run.tokens_used} tokens · ${run.cost}</span>
                <Badge className={statusColors[run.status] || "bg-gray-600"}>{run.status}</Badge>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
