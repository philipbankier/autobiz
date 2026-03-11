"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { CompanyCard } from "@/components/company/company-card";
import { CompanyStatus } from "@/types";
import type { Company } from "@/types";
import { Plus } from "lucide-react";

const mockCompanies: Company[] = [
  {
    id: "comp-1",
    name: "NexGen AI Solutions",
    slug: "nexgen-ai-solutions",
    mission:
      "Provide cutting-edge AI consulting and automation solutions for mid-market businesses looking to scale operations.",
    status: CompanyStatus.ACTIVE,
    owner_id: "user-1",
    created_at: "2026-02-15T00:00:00Z",
    updated_at: "2026-03-11T00:00:00Z",
  },
  {
    id: "comp-2",
    name: "EcoTrack Analytics",
    slug: "ecotrack-analytics",
    mission:
      "AI-powered environmental monitoring and sustainability reporting for enterprise companies.",
    status: CompanyStatus.ACTIVE,
    owner_id: "user-1",
    created_at: "2026-03-01T00:00:00Z",
    updated_at: "2026-03-10T00:00:00Z",
  },
  {
    id: "comp-3",
    name: "SwiftShip Logistics",
    slug: "swiftship-logistics",
    mission:
      "Autonomous logistics optimization using AI to reduce delivery times and costs by 40%.",
    status: CompanyStatus.PENDING,
    owner_id: "user-1",
    created_at: "2026-03-10T00:00:00Z",
    updated_at: "2026-03-10T00:00:00Z",
  },
];

export default function DashboardPage() {
  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Your Companies</h1>
          <p className="text-muted-foreground mt-1">
            Manage your AI-powered businesses
          </p>
        </div>
        <Link href="/dashboard/new">
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            New Company
          </Button>
        </Link>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {mockCompanies.map((company) => (
          <CompanyCard key={company.id} company={company} />
        ))}
      </div>
    </div>
  );
}
