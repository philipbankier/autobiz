"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getCompanies, type Company } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const statusColors: Record<string, string> = {
  planning: "bg-yellow-600",
  building: "bg-blue-600",
  running: "bg-green-600",
  paused: "bg-gray-600",
  archived: "bg-red-600",
};

export default function DashboardPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCompanies().then((res) => {
      if (res.data) setCompanies(res.data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <p className="text-gray-400">Loading companies...</p>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Your Companies</h1>
        <Link href="/dashboard/new">
          <Button>+ New Company</Button>
        </Link>
      </div>

      {companies.length === 0 ? (
        <Card className="p-12 bg-gray-900 border-gray-800 text-center">
          <p className="text-gray-400 mb-4">No companies yet. Launch your first autonomous business!</p>
          <Link href="/dashboard/new">
            <Button>Create Company</Button>
          </Link>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {companies.map((company) => (
            <Link key={company.id} href={`/dashboard/${company.id}`}>
              <Card className="p-6 bg-gray-900 border-gray-800 hover:border-gray-700 transition-colors cursor-pointer">
                <div className="flex items-start justify-between mb-2">
                  <h2 className="text-lg font-semibold text-white">{company.name}</h2>
                  <Badge className={statusColors[company.status] || "bg-gray-600"}>
                    {company.status}
                  </Badge>
                </div>
                <p className="text-gray-400 text-sm mb-3">{company.mission}</p>
                <p className="text-gray-500 text-xs">
                  {company.slug}.autobiz.app · Created{" "}
                  {new Date(company.created_at).toLocaleDateString()}
                </p>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
