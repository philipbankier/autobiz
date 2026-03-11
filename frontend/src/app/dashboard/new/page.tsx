"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createCompany } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

export default function NewCompanyPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [mission, setMission] = useState("");
  const [slug, setSlug] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleNameChange(value: string) {
    setName(value);
    // Auto-generate slug from name
    setSlug(value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const res = await createCompany(name, mission, slug);
    setLoading(false);

    if (res.error || !res.data) {
      setError(res.error || "Failed to create company");
      return;
    }

    router.push(`/dashboard/${res.data.id}`);
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Launch a New Company</h1>

      <Card className="p-8 bg-gray-900 border-gray-800">
        {error && (
          <div className="bg-red-900/30 border border-red-800 text-red-300 px-4 py-2 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Company Name</label>
            <Input
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder="SocialPilot AI"
              required
              className="bg-gray-800 border-gray-700 text-white"
            />
          </div>

          <div>
            <label className="text-sm text-gray-400 mb-1 block">Mission</label>
            <Textarea
              value={mission}
              onChange={(e) => setMission(e.target.value)}
              placeholder="AI-powered social media management for solo founders. Automatically creates, schedules, and publishes content across all platforms."
              required
              rows={3}
              className="bg-gray-800 border-gray-700 text-white"
            />
            <p className="text-gray-600 text-xs mt-1">Describe what this business does. Agents will use this to guide their work.</p>
          </div>

          <div>
            <label className="text-sm text-gray-400 mb-1 block">Slug</label>
            <div className="flex items-center gap-2">
              <Input
                value={slug}
                onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""))}
                placeholder="socialpilot"
                required
                className="bg-gray-800 border-gray-700 text-white"
              />
              <span className="text-gray-500 text-sm whitespace-nowrap">.autobiz.app</span>
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={loading} className="flex-1">
              {loading ? "Creating..." : "🚀 Launch Company"}
            </Button>
            <Button type="button" variant="outline" onClick={() => router.back()}>
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
