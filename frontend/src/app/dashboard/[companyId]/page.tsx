"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getCompany, getDashboard, getDepartments, type Company, type Department } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DepartmentCard } from "@/components/dashboard/department-card";
import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { SteeringEditor } from "@/components/dashboard/steering-editor";
import { SchedulerControls } from "@/components/dashboard/scheduler-controls";

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
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getCompany(companyId),
      getDashboard(companyId),
      getDepartments(companyId),
    ]).then(([compRes, dashRes, deptRes]) => {
      if (compRes.data) setCompany(compRes.data);
      if (dashRes.data) setDashboard(dashRes.data as unknown as DashboardData);
      if (deptRes.data) setDepartments(deptRes.data);
      setLoading(false);
    });
  }, [companyId]);

  if (loading) return <p className="text-gray-400">Loading...</p>;
  if (!company || !dashboard) return <p className="text-red-400">Company not found</p>;

  // Merge dashboard dept data with full department records
  const deptCards = dashboard.departments.map((dd) => {
    const full = departments.find((d) => d.type === dd.type);
    const lastRun = dashboard.recent_runs.find((r) => r.department === dd.type);
    return {
      type: dd.type,
      status: dd.status,
      autonomy: dd.autonomy,
      budget_cap_daily: full?.budget_cap_daily || null,
      cost_today: dashboard.cost_by_department[dd.type] || 0,
      last_run_at: lastRun?.started_at || null,
      last_run_status: lastRun?.status || null,
      current_task: lastRun?.summary || null,
    };
  });

  const profit = parseFloat(dashboard.profit);

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
        </div>
        <div className="text-right">
          <p className="text-gray-500 text-xs">Credits</p>
          <p className="text-2xl font-bold text-green-400">${dashboard.credits_balance}</p>
        </div>
      </div>

      {/* Row 1: P&L Summary + Scheduler Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* P&L compact */}
        <div className="lg:col-span-2">
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
              <p className="text-gray-500 text-xs">Cost</p>
              <p className="text-xl font-bold text-red-400">${dashboard.total_cost}</p>
            </Card>
            <Card className="p-3 bg-gray-900 border-gray-800">
              <p className="text-gray-500 text-xs">Profit</p>
              <p className={`text-xl font-bold ${profit >= 0 ? "text-green-400" : "text-red-400"}`}>
                ${dashboard.profit}
              </p>
            </Card>
          </div>
        </div>

        {/* Scheduler */}
        <div>
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Automation</h2>
          <SchedulerControls companyId={companyId} />
        </div>
      </div>

      {/* Row 2: Department Cards */}
      <div>
        <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Departments</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {deptCards.map((dept) => (
            <DepartmentCard key={dept.type} companyId={companyId} department={dept} />
          ))}
        </div>
      </div>

      {/* Row 3: Activity Feed + STEERING.md Editor */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Live Activity</h2>
          <ActivityFeed companyId={companyId} />
        </div>
        <div>
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Configuration</h2>
          <SteeringEditor companyId={companyId} />
        </div>
      </div>
    </div>
  );
}
