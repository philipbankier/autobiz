"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { ArrowRight, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ProgressStep, type StepStatus } from "./progress-step";
import { connectActivityStream, getCompanyFile } from "@/lib/api";

interface OnboardingStep {
  key: string;
  label: string;
  status: StepStatus;
  detail?: string;
}

const INITIAL_STEPS: OnboardingStep[] = [
  { key: "workspace", label: "Company workspace created", status: "pending" },
  { key: "github", label: "GitHub repository created", status: "pending" },
  { key: "vercel", label: "Vercel project linked", status: "pending" },
  { key: "ceo_analysis", label: "CEO agent analyzing your idea...", status: "pending" },
  { key: "business_plan", label: "Business plan generated!", status: "pending" },
  { key: "departments", label: "Department tasks created", status: "pending" },
];

// Map SSE event types/messages to step keys
function matchEventToStep(event: SSEEvent): string | null {
  const text = (event.data || event.summary || event.message || "").toLowerCase();
  if (text.includes("workspace") || text.includes("provision") || event.type === "company.provisioned") return "workspace";
  if (text.includes("github") || text.includes("repo") || event.type === "git.repo_created") return "github";
  if (text.includes("vercel") || text.includes("deploy") || event.type === "deploy.linked") return "vercel";
  if (text.includes("analy") || text.includes("ceo") || event.type === "agent.run_started") return "ceo_analysis";
  if (text.includes("business plan") || text.includes("company.md") || event.type === "agent.run_completed") return "business_plan";
  if (text.includes("department") || text.includes("task") || event.type === "onboard.completed") return "departments";
  return null;
}

interface SSEEvent {
  type?: string;
  data?: string;
  summary?: string;
  message?: string;
  [key: string]: unknown;
}

interface StepProgressProps {
  companyId: string;
  onComplete: () => void;
}

export function StepProgress({ companyId, onComplete }: StepProgressProps) {
  const [steps, setSteps] = useState<OnboardingStep[]>(INITIAL_STEPS);
  const [companyMd, setCompanyMd] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const completedKeysRef = useRef<Set<string>>(new Set());

  const markStep = useCallback((key: string, status: StepStatus, detail?: string) => {
    completedKeysRef.current.add(key);
    setSteps((prev) => {
      const updated = prev.map((s) =>
        s.key === key ? { ...s, status, detail } : s
      );
      // Set the next pending step as active
      const firstPending = updated.findIndex((s) => s.status === "pending");
      if (firstPending !== -1) {
        updated[firstPending] = { ...updated[firstPending], status: "active" };
      }
      return updated;
    });
  }, []);

  useEffect(() => {
    // Start the first step as active immediately
    setSteps((prev) => {
      const copy = [...prev];
      copy[0] = { ...copy[0], status: "active" };
      return copy;
    });

    const es = connectActivityStream(companyId, (event: SSEEvent) => {
      const stepKey = matchEventToStep(event);
      if (stepKey) {
        markStep(stepKey, "complete", event.summary || event.message);
      }

      // Check for completion
      if (
        event.type === "onboard.completed" ||
        event.type === "stream.complete" ||
        completedKeysRef.current.size >= INITIAL_STEPS.length
      ) {
        // Mark all remaining as complete
        setSteps((prev) => prev.map((s) => (s.status !== "complete" ? { ...s, status: "complete" } : s)));
        setDone(true);

        // Fetch COMPANY.md
        getCompanyFile(companyId, "COMPANY.md").then((res) => {
          if (res.data?.content) {
            setCompanyMd(res.data.content);
          }
        });
      }

      if (event.type === "error") {
        setError(event.message || event.data || "An error occurred during onboarding");
      }
    });

    eventSourceRef.current = es;

    // Timeout: if not done in 3 minutes, mark as complete anyway
    const timeout = setTimeout(() => {
      setSteps((prev) => prev.map((s) => (s.status !== "complete" ? { ...s, status: "complete" } : s)));
      setDone(true);
    }, 180_000);

    return () => {
      es.close();
      clearTimeout(timeout);
    };
  }, [companyId, markStep]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-white mb-1">
          {done ? "Your company is ready!" : "Setting up your company..."}
        </h2>
        <p className="text-gray-400 text-sm">
          {done
            ? "The CEO agent has finished building your business."
            : "Watch as the CEO agent builds your business in real-time."}
        </p>
      </div>

      <Card className="bg-gray-900/50 border-gray-800 overflow-hidden">
        <div className="p-2">
          {steps.map((step) => (
            <ProgressStep
              key={step.key}
              label={step.label}
              status={step.status}
              detail={step.detail}
            />
          ))}
        </div>
      </Card>

      {error && (
        <div className="bg-red-900/20 border border-red-800/50 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-300 text-sm">{error}</p>
            <Button
              variant="ghost"
              size="sm"
              className="mt-2 text-red-300 hover:text-red-200"
              onClick={() => window.location.reload()}
            >
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
              Retry
            </Button>
          </div>
        </div>
      )}

      {companyMd && (
        <Card className="bg-gray-900/50 border-gray-800 p-5">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Generated Business Plan</p>
          <div className="prose prose-invert prose-sm max-w-none text-gray-300 whitespace-pre-wrap font-mono text-xs leading-relaxed max-h-64 overflow-y-auto">
            {companyMd}
          </div>
        </Card>
      )}

      {done && (
        <div className="flex justify-end">
          <Button onClick={onComplete} size="lg">
            Go to Dashboard
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
