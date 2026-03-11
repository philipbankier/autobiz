"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { DepartmentType, AutonomyLevel, DepartmentStatus } from "@/types";
import type { Department } from "@/types";
import { Save } from "lucide-react";

const autonomyOptions = Object.values(AutonomyLevel).map((a) => ({
  value: a,
  label: a.charAt(0).toUpperCase() + a.slice(1),
}));

const statusOptions = Object.values(DepartmentStatus).map((s) => ({
  value: s,
  label: s.charAt(0).toUpperCase() + s.slice(1),
}));

const mockDepartments: Department[] = [
  {
    id: "dept-1",
    company_id: "comp-1",
    type: DepartmentType.MARKETING,
    autonomy_level: AutonomyLevel.HIGH,
    status: DepartmentStatus.ACTIVE,
    budget_cap: 500,
    config: {},
    created_at: "2026-02-15T00:00:00Z",
    updated_at: "2026-03-11T00:00:00Z",
  },
  {
    id: "dept-2",
    company_id: "comp-1",
    type: DepartmentType.SALES,
    autonomy_level: AutonomyLevel.MEDIUM,
    status: DepartmentStatus.ACTIVE,
    budget_cap: 750,
    config: {},
    created_at: "2026-02-15T00:00:00Z",
    updated_at: "2026-03-11T00:00:00Z",
  },
  {
    id: "dept-3",
    company_id: "comp-1",
    type: DepartmentType.CUSTOMER_SUPPORT,
    autonomy_level: AutonomyLevel.FULL,
    status: DepartmentStatus.ACTIVE,
    budget_cap: 1000,
    config: {},
    created_at: "2026-02-15T00:00:00Z",
    updated_at: "2026-03-11T00:00:00Z",
  },
  {
    id: "dept-4",
    company_id: "comp-1",
    type: DepartmentType.PRODUCT,
    autonomy_level: AutonomyLevel.MEDIUM,
    status: DepartmentStatus.ACTIVE,
    budget_cap: 300,
    config: {},
    created_at: "2026-02-15T00:00:00Z",
    updated_at: "2026-03-11T00:00:00Z",
  },
  {
    id: "dept-5",
    company_id: "comp-1",
    type: DepartmentType.ENGINEERING,
    autonomy_level: AutonomyLevel.LOW,
    status: DepartmentStatus.PAUSED,
    budget_cap: 2000,
    config: {},
    created_at: "2026-02-15T00:00:00Z",
    updated_at: "2026-03-11T00:00:00Z",
  },
  {
    id: "dept-6",
    company_id: "comp-1",
    type: DepartmentType.RESEARCH,
    autonomy_level: AutonomyLevel.HIGH,
    status: DepartmentStatus.ACTIVE,
    budget_cap: 400,
    config: {},
    created_at: "2026-02-15T00:00:00Z",
    updated_at: "2026-03-11T00:00:00Z",
  },
];

function statusVariant(status: DepartmentStatus) {
  switch (status) {
    case DepartmentStatus.ACTIVE:
      return "success" as const;
    case DepartmentStatus.PAUSED:
      return "warning" as const;
    case DepartmentStatus.DISABLED:
      return "destructive" as const;
  }
}

function DepartmentCard({ department }: { department: Department }) {
  const [autonomy, setAutonomy] = useState(department.autonomy_level);
  const [budget, setBudget] = useState(String(department.budget_cap || ""));
  const [status, setStatus] = useState(department.status);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base capitalize">
              {department.type.replace("_", " ")}
            </CardTitle>
            <CardDescription className="text-xs mt-1">
              ID: {department.id}
            </CardDescription>
          </div>
          <Badge variant={statusVariant(status)}>{status}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">
              Autonomy Level
            </label>
            <Select
              options={autonomyOptions}
              value={autonomy}
              onChange={(e) => setAutonomy(e.target.value as AutonomyLevel)}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">
              Budget Cap (USD/mo)
            </label>
            <Input
              type="number"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              placeholder="No limit"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">
              Status
            </label>
            <Select
              options={statusOptions}
              value={status}
              onChange={(e) => setStatus(e.target.value as DepartmentStatus)}
            />
          </div>
        </div>
        <div className="flex justify-end">
          <Button size="sm" variant="outline" className="gap-2">
            <Save className="h-3.5 w-3.5" />
            Save Changes
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function SettingsPage() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Department Settings</h2>
        <p className="text-sm text-muted-foreground">
          Configure autonomy levels, budgets, and status for each department
        </p>
      </div>
      <div className="space-y-4">
        {mockDepartments.map((dept) => (
          <DepartmentCard key={dept.id} department={dept} />
        ))}
      </div>
    </div>
  );
}
