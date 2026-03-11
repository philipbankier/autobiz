"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getCompany, getDashboard, type Company } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const deptIcons: Record<string, string> = {
  ceo: "👔", developer: "💻", marketing: "📢", sales: "💰", finance: "📊", support: "🎧",
};
const statusColors: Record<string, string> = {
  idle: "text-gray-400", running: "text-green-400", waiting: "text-yellow-400",
};
const runStatusColors: Record<string, string> = {
  completed: "bg-green-600", failed: "bg-red-600", running: "bg-blue-600",
};

interface DashboardData {
  company_status: string;
  departments: { type: string; status: string; autonomy: string }[];
  active_runs: number;
  completed_runs: number;
  runs_today: number;
  failed_runs: number;
  task_stats: Record<string, number>;
  total_tasks: number;
  total_cost: string;
  cost_today: string;
  cost_this_week: string;
  cost_by_department: Record<string, number>;
  total_revenue: string;
  mrr: string;
  customers: number;
  profit: string;
  knowledge_graph: { entities: number; relations: number; types: Record<string, number> };
  credits_balance: string;
  recent_runs: { id: string; department: string; status: string; started_at: string; summary: string | null; cost: string }[];
}

export default function CompanyOverviewPage() {
  const params = useParams();
  const companyId = params.companyId as string;
  const [company, setCompany] = useState<Company | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getCompany(companyId), getDashboard(companyId)]).then(([compRes, dashRes]) => {
      if (compRes.data) setCompany(compRes.data);
      if (dashRes.data) setDashboard(dashRes.data as unknown as DashboardData);
      setLoading(false);
    });
  }, [companyId]);

  if (loading) return <p className="text-gray-400">Loading...</p>;
  if (!company || !dashboard) return <p className="text-red-400">Company not found</p>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-white">{company.name}</h1>
            <Badge>{company.status}</Badge>
          </div>
          <p className="text-gray-400">{company.mission}</p>
          <p className="text-gray-600 text-sm mt-1">{company.slug}.autobiz.app</p>
        </div>
        <div className="text-right">
          <p className="text-gray-500 text-xs">Credits</p>
          <p className="text-2xl font-bold text-green-400">${dashboard.credits_balance}</p>
        </div>
      </div>

      {/* Financial Overview */}
      <div>
        <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">P&L</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Card className="p-3 bg-gray-900 border-gray-800">
            <p className="text-gray-500 text-xs">Revenue</p>
            <p className="text-xl font-bold text-green-400">${dashboard.total_revenue}</p>
          </Card>
          <Card className="p-3 bg-gray-900 border-gray-800">
            <p className="text-gray-500 text-xs">MRR</p>
            <p className="text-xl font-bold text-green-400">${dashboard.mrr}</p>
          </Card>
          <Card className="p-3 bg-gray-900 border-gray-800">
            <p className="text-gray-500 text-xs">Customers</p>
            <p className="text-xl font-bold text-white">{dashboard.customers}</p>
          </Card>
          <Card className="p-3 bg-gray-900 border-gray-800">
            <p className="text-gray-500 text-xs">Total Cost</p>
            <p className="text-xl font-bold text-red-400">${dashboard.total_cost}</p>
          </Card>
          <Card className="p-3 bg-gray-900 border-gray-800">
            <p className="text-gray-500 text-xs">Profit</p>
            <p className={`text-xl font-bold ${parseFloat(dashboard.profit) >= 0 ? "text-green-400" : "text-red-400"}`}>
              ${dashboard.profit}
            </p>
          </Card>
        </div>
      </div>

      {/* Agent Metrics */}
      <div>
        <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Agent Activity</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card className="p-3 bg-gray-900 border-gray-800">
            <p className="text-gray-500 text-xs">Active Now</p>
            <p className="text-xl font-bold text-blue-400">{dashboard.active_runs}</p>
          </Card>
          <Card className="p-3 bg-gray-900 border-gray-800">
            <p className="text-gray-500 text-xs">Runs Today</p>
            <p className="text-xl font-bold text-white">{dashboard.runs_today}</p>
          </Card>
          <Card className="p-3 bg-gray-900 border-gray-800">
            <p className="text-gray-500 text-xs">Total Completed</p>
            <p className="text-xl font-bold text-green-400">{dashboard.completed_runs}</p>
          </Card>
          <Card className="p-3 bg-gray-900 border-gray-800">
            <p className="text-gray-500 text-xs">Failed</p>
            <p className="text-xl font-bold text-red-400">{dashboard.failed_runs}</p>
          </Card>
        </div>
      </div>

      {/* Cost by Department + Tasks */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Cost Breakdown */}
        <div>
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Cost by Department</h2>
          <Card className="p-4 bg-gray-900 border-gray-800">
            <div className="flex justify-between text-xs text-gray-500 mb-2">
              <span>Today: ${dashboard.cost_today}</span>
              <span>This Week: ${dashboard.cost_this_week}</span>
            </div>
            {Object.entries(dashboard.cost_by_department).length > 0 ? (
              <div className="space-y-2">
                {Object.entries(dashboard.cost_by_department).map(([dept, cost]) => (
                  <div key={dept} className="flex items-center justify-between">
                    <span className="text-gray-300 text-sm capitalize">
                      {deptIcons[dept] || "🏢"} {dept}
                    </span>
                    <span className="text-gray-400 text-sm">${cost.toFixed(4)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600 text-sm">No costs recorded yet</p>
            )}
          </Card>
        </div>

        {/* Task Stats */}
        <div>
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Tasks ({dashboard.total_tasks})</h2>
          <Card className="p-4 bg-gray-900 border-gray-800">
            <div className="space-y-2">
              {["todo", "in_progress", "done", "blocked"].map((status) => (
                <div key={status} className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm capitalize">{status.replace("_", " ")}</span>
                  <span className="text-gray-400 text-sm">{dashboard.task_stats[status] || 0}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Department Status Grid */}
      <div>
        <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Departments</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {dashboard.departments.map((dept) => (
            <Card key={dept.type} className="p-3 bg-gray-900 border-gray-800">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{deptIcons[dept.type] || "🏢"}</span>
                  <span className="text-white font-medium capitalize">{dept.type}</span>
                </div>
                <span className={`text-xs ${statusColors[dept.status] || "text-gray-400"}`}>
                  ● {dept.status}
                </span>
              </div>
              <span className="text-gray-500 text-xs capitalize">{dept.autonomy.replace("_", " ")}</span>
            </Card>
          ))}
        </div>
      </div>

      {/* Knowledge Graph */}
      <div>
        <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Knowledge Graph</h2>
        <Card className="p-4 bg-gray-900 border-gray-800">
          <div className="flex gap-6 mb-3">
            <div>
              <span className="text-gray-500 text-xs">Entities</span>
              <p className="text-xl font-bold text-purple-400">{dashboard.knowledge_graph.entities}</p>
            </div>
            <div>
              <span className="text-gray-500 text-xs">Relations</span>
              <p className="text-xl font-bold text-purple-400">{dashboard.knowledge_graph.relations}</p>
            </div>
          </div>
          {Object.entries(dashboard.knowledge_graph.types).length > 0 && (
            <div className="flex flex-wrap gap-2">
              {Object.entries(dashboard.knowledge_graph.types).map(([type, count]) => (
                <Badge key={type} className="bg-purple-900/50 text-purple-300">
                  {type}: {count}
                </Badge>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Recent Activity */}
      {dashboard.recent_runs.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Recent Agent Runs</h2>
          <div className="space-y-2">
            {dashboard.recent_runs.map((run) => (
              <Card key={run.id} className="p-3 bg-gray-900 border-gray-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span>{deptIcons[run.department] || "🤖"}</span>
                  <div>
                    <p className="text-white text-sm">
                      {run.summary || `${run.department} run`}
                    </p>
                    <p className="text-gray-500 text-xs">
                      {run.started_at ? new Date(run.started_at).toLocaleString() : ""}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400 text-xs">${run.cost}</span>
                  <Badge className={runStatusColors[run.status] || "bg-gray-600"}>
                    {run.status}
                  </Badge>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
