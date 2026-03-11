"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getCompany, getDashboard, type Company, type DashboardData } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const deptIcons: Record<string, string> = {
  ceo: "👔", developer: "💻", marketing: "📢", sales: "💰", finance: "📊", support: "🎧",
};

const statusColors: Record<string, string> = {
  idle: "text-gray-400", running: "text-green-400", waiting: "text-yellow-400",
};

export default function CompanyOverviewPage() {
  const params = useParams();
  const companyId = params.companyId as string;
  const [company, setCompany] = useState<Company | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getCompany(companyId), getDashboard(companyId)]).then(([compRes, dashRes]) => {
      if (compRes.data) setCompany(compRes.data);
      if (dashRes.data) setDashboard(dashRes.data);
      setLoading(false);
    });
  }, [companyId]);

  if (loading) return <p className="text-gray-400">Loading...</p>;
  if (!company || !dashboard) return <p className="text-red-400">Company not found</p>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-2xl font-bold text-white">{company.name}</h1>
          <Badge>{company.status}</Badge>
        </div>
        <p className="text-gray-400">{company.mission}</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4 bg-gray-900 border-gray-800">
          <p className="text-gray-500 text-xs uppercase">Active Runs</p>
          <p className="text-2xl font-bold text-white">{dashboard.active_runs}</p>
        </Card>
        <Card className="p-4 bg-gray-900 border-gray-800">
          <p className="text-gray-500 text-xs uppercase">Completed</p>
          <p className="text-2xl font-bold text-white">{dashboard.completed_runs}</p>
        </Card>
        <Card className="p-4 bg-gray-900 border-gray-800">
          <p className="text-gray-500 text-xs uppercase">Total Cost</p>
          <p className="text-2xl font-bold text-white">${dashboard.total_cost}</p>
        </Card>
        <Card className="p-4 bg-gray-900 border-gray-800">
          <p className="text-gray-500 text-xs uppercase">Credits</p>
          <p className="text-2xl font-bold text-green-400">${dashboard.credits_balance}</p>
        </Card>
      </div>

      {/* Department Status Grid */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">Departments</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {dashboard.departments.map((dept) => (
            <Card key={dept.type} className="p-4 bg-gray-900 border-gray-800">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{deptIcons[dept.type] || "🏢"}</span>
                <span className="text-white font-medium capitalize">{dept.type}</span>
              </div>
              <span className={`text-sm ${statusColors[dept.status] || "text-gray-400"}`}>
                ● {dept.status}
              </span>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
