"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { createCompany } from "@/lib/api";
import { Loader2 } from "lucide-react";

export function CreateCompanyForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [mission, setMission] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleNameChange(value: string) {
    setName(value);
    setSlug(
      value
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, "")
        .replace(/\s+/g, "-")
        .replace(/-+/g, "-")
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const result = await createCompany({ name, slug, mission });

    if (result.error) {
      setError(result.error);
      setLoading(false);
      return;
    }

    if (result.data) {
      router.push(`/dashboard/${result.data.id}`);
    }
  }

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl">Create Your AI Company</CardTitle>
        <CardDescription>
          Set up a new AI-powered business. Your departments will begin working autonomously
          once configured.
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="name">
              Company Name
            </label>
            <Input
              id="name"
              placeholder="My AI Startup"
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="slug">
              Slug
            </label>
            <Input
              id="slug"
              placeholder="my-ai-startup"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              required
            />
            <p className="text-xs text-muted-foreground">
              URL-friendly identifier. Auto-generated from name.
            </p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="mission">
              Mission Statement
            </label>
            <Textarea
              id="mission"
              placeholder="Describe what your AI company will do..."
              value={mission}
              onChange={(e) => setMission(e.target.value)}
              rows={4}
              required
            />
          </div>
        </CardContent>
        <CardFooter>
          <Button type="submit" disabled={loading} className="w-full">
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Create Company
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
