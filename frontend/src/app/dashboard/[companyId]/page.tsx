"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getCompany,
  getDashboard,
  getActivityEvents,
  type Company,
} from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Globe,
  CreditCard,
  CheckCircle2,
  Clock,
  MessageCircle,
  ExternalLink,
  Loader2,
} from "lucide-react";

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
  knowledge_graph: {
    entities: number;
    relations: number;
    types: Record<string, number>;
  };
  credits_balance: string;
  recent_runs: {
    id: string;
    department: string;
    status: string;
    started_at: string;
    summary: string | null;
    cost: string;
  }[];
}

interface ActivityEvent {
  id: string;
  event_type: string;
  department?: string;
  summary?: string;
  created_at: string;
}

const statusColors: Record<string, string> = {
  planning: "bg-yellow-500/20 text-yellow-400",
  building: "bg-emerald-500/20 text-emerald-400",
  running: "bg-emerald-500/20 text-emerald-400",
  live: "bg-emerald-500/20 text-emerald-400",
  paused: "bg-gray-500/20 text-gray-400",
  archived: "bg-gray-500/20 text-gray-400",
};

function humanizeEvent(event: ActivityEvent): string {
  const dept = event.department;
  const deptLabel = dept
    ? dept.charAt(0).toUpperCase() + dept.slice(1)
    : "Your team";

  if (event.summary) {
    return event.summary;
  }

  switch (event.event_type) {
    case "run_completed":
      return `${deptLabel} finished a task`;
    case "run_started":
      return `${deptLabel} started working`;
    case "run_failed":
      return `${deptLabel} ran into an issue`;
    case "task_created":
      return `New task created for ${deptLabel}`;
    case "department_triggered":
      return `${deptLabel} was activated`;
    default:
      return `${deptLabel} activity`;
  }
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function CompanyOverviewPage() {
  const params = useParams();
  const companyId = params.companyId as string;
  const [company, setCompany] = useState<Company | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getCompany(companyId),
      getDashboard(companyId),
      getActivityEvents(companyId),
    ]).then(([compRes, dashRes, actRes]) => {
      if (compRes.data) setCompany(compRes.data);
      if (dashRes.data)
        setDashboard(dashRes.data as unknown as DashboardData);
      if (actRes.data)
        setActivity(
          (actRes.data as unknown as ActivityEvent[]).slice(0, 5)
        );
      setLoading(false);
    });
  }, [companyId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-emerald-500" />
      </div>
    );
  }

  if (!company || !dashboard) {
    return <p className="text-red-400">Company not found</p>;
  }

  const statusClass =
    statusColors[company.status] || "bg-gray-500/20 text-gray-400";

  const websiteReady =
    company.status === "running" || company.status === "live";
  const paymentsReady = parseFloat(dashboard.total_revenue) > 0 || websiteReady;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-white">{company.name}</h1>
            <Badge className={statusClass}>
              {company.status === "running" || company.status === "live"
                ? "Live"
                : company.status === "planning" || company.status === "building"
                ? "Building"
                : company.status === "paused"
                ? "Paused"
                : company.status}
            </Badge>
          </div>
          <p className="text-gray-400">{company.mission}</p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-4 bg-gray-900 border-gray-800">
          <div className="flex items-center gap-3">
            <Globe className="h-5 w-5 text-emerald-400" />
            <div>
              <p className="text-xs text-gray-500">Website</p>
              <p className="text-sm font-medium text-white">
                {websiteReady ? "Live" : "Building..."}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4 bg-gray-900 border-gray-800">
          <div className="flex items-center gap-3">
            <CreditCard className="h-5 w-5 text-emerald-400" />
            <div>
              <p className="text-xs text-gray-500">Payments</p>
              <p className="text-sm font-medium text-white">
                {paymentsReady ? "Active" : "Setting up..."}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4 bg-gray-900 border-gray-800">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            <div>
              <p className="text-xs text-gray-500">Tasks Completed</p>
              <p className="text-sm font-medium text-white">
                {dashboard.completed_runs}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* My Website */}
        <Card className="p-6 bg-gray-900 border-gray-800">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Globe className="h-5 w-5 text-emerald-400" />
            My Website
          </h2>
          {websiteReady ? (
            <div className="space-y-3">
              <p className="text-sm text-gray-400">
                Your website is live and ready to share.
              </p>
              {company.slug && (
                <a
                  href={`https://${company.slug}.autobiz.app`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-emerald-400 hover:text-emerald-300 text-sm"
                >
                  {company.slug}.autobiz.app
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-gray-400">
                Your website is being built...
              </p>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div className="bg-emerald-500 h-2 rounded-full w-1/3 animate-pulse" />
              </div>
            </div>
          )}
        </Card>

        {/* My Payments */}
        <Card className="p-6 bg-gray-900 border-gray-800">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-emerald-400" />
            My Payments
          </h2>
          {paymentsReady ? (
            <div className="space-y-3">
              <p className="text-sm text-gray-400">
                Stripe is connected. You can accept payments.
              </p>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-gray-500">
                  Revenue:{" "}
                  <span className="text-white font-medium">
                    ${dashboard.total_revenue}
                  </span>
                </span>
                <span className="text-gray-500">
                  Customers:{" "}
                  <span className="text-white font-medium">
                    {dashboard.customers}
                  </span>
                </span>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-gray-400">
                Payment processing is being configured...
              </p>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div className="bg-emerald-500 h-2 rounded-full w-1/4 animate-pulse" />
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className="p-6 bg-gray-900 border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Clock className="h-5 w-5 text-emerald-400" />
          Recent Activity
        </h2>
        {activity.length > 0 ? (
          <div className="space-y-3">
            {activity.map((event) => (
              <div
                key={event.id}
                className="flex items-start justify-between py-2 border-b border-gray-800 last:border-0"
              >
                <p className="text-sm text-gray-300">
                  {humanizeEvent(event)}
                </p>
                <span className="text-xs text-gray-600 shrink-0 ml-4">
                  {timeAgo(event.created_at)}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">
            No activity yet. Your AI team will get started soon.
          </p>
        )}
      </Card>

      {/* Floating Chat Button */}
      <Link href={`/dashboard/${companyId}/chat`}>
        <Button className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-500/20 p-0">
          <MessageCircle className="h-6 w-6" />
        </Button>
      </Link>
    </div>
  );
}
