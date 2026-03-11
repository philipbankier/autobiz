"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getDepartments, updateDepartment, triggerDepartment, type Department } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const deptIcons: Record<string, string> = {
  ceo: "👔", developer: "💻", marketing: "📢", sales: "💰", finance: "📊", support: "🎧",
};
const autonomyLevels = ["full_auto", "notify", "approve", "manual"];

export default function SettingsPage() {
  const params = useParams();
  const companyId = params.companyId as string;
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [triggering, setTriggering] = useState<string | null>(null);

  useEffect(() => {
    getDepartments(companyId).then((res) => {
      if (res.data) setDepartments(res.data);
      setLoading(false);
    });
  }, [companyId]);

  async function handleUpdate(dept: Department, field: string, value: string | number | null) {
    setSaving(dept.type);
    await updateDepartment(companyId, dept.type, { [field]: value });
    // Refresh
    const res = await getDepartments(companyId);
    if (res.data) setDepartments(res.data);
    setSaving(null);
  }

  async function handleTrigger(deptType: string) {
    setTriggering(deptType);
    await triggerDepartment(companyId, deptType);
    setTriggering(null);
  }

  if (loading) return <p className="text-gray-400">Loading settings...</p>;

  return (
    <div>
      <h2 className="text-lg font-semibold text-white mb-4">Department Settings</h2>

      <div className="space-y-3">
        {departments.map((dept) => (
          <Card key={dept.id} className="p-4 bg-gray-900 border-gray-800">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-3 min-w-[140px]">
                <span className="text-lg">{deptIcons[dept.type] || "🏢"}</span>
                <div>
                  <p className="text-white font-medium capitalize">{dept.type}</p>
                  <p className="text-gray-500 text-xs">● {dept.status}</p>
                </div>
              </div>

              <div className="flex items-center gap-4 flex-wrap">
                <div>
                  <label className="text-gray-500 text-xs block mb-1">Autonomy</label>
                  <select
                    value={dept.autonomy_level}
                    onChange={(e) => handleUpdate(dept, "autonomy_level", e.target.value)}
                    className="bg-gray-800 border border-gray-700 text-white rounded px-2 py-1 text-sm"
                    disabled={saving === dept.type}
                  >
                    {autonomyLevels.map((l) => (
                      <option key={l} value={l}>{l.replace("_", " ")}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-gray-500 text-xs block mb-1">Daily Budget ($)</label>
                  <Input
                    type="number"
                    step="0.50"
                    min="0"
                    placeholder="No limit"
                    defaultValue={dept.budget_cap_daily || ""}
                    onBlur={(e) => {
                      const val = e.target.value ? parseFloat(e.target.value) : null;
                      handleUpdate(dept, "budget_cap_daily", val);
                    }}
                    className="w-24 bg-gray-800 border-gray-700 text-white text-sm"
                    disabled={saving === dept.type}
                  />
                </div>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleTrigger(dept.type)}
                  disabled={triggering === dept.type}
                >
                  {triggering === dept.type ? "Running..." : "▶ Trigger"}
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
