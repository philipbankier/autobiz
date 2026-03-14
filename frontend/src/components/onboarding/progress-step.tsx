"use client";

import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export type StepStatus = "pending" | "active" | "complete" | "error";

interface ProgressStepProps {
  label: string;
  status: StepStatus;
  detail?: string;
}

export function ProgressStep({ label, status, detail }: ProgressStepProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 py-3 px-4 rounded-lg transition-all duration-500",
        status === "active" && "bg-indigo-950/40",
        status === "complete" && "opacity-80",
        status === "pending" && "opacity-40"
      )}
    >
      <div className="mt-0.5 flex-shrink-0">
        {status === "complete" && (
          <CheckCircle2 className="h-5 w-5 text-green-400" />
        )}
        {status === "active" && (
          <Loader2 className="h-5 w-5 text-indigo-400 animate-spin" />
        )}
        {status === "pending" && (
          <Circle className="h-5 w-5 text-gray-600" />
        )}
        {status === "error" && (
          <Circle className="h-5 w-5 text-red-400" />
        )}
      </div>
      <div className="min-w-0">
        <p
          className={cn(
            "text-sm font-medium",
            status === "complete" && "text-green-300",
            status === "active" && "text-indigo-300",
            status === "pending" && "text-gray-500",
            status === "error" && "text-red-300"
          )}
        >
          {label}
        </p>
        {detail && (
          <p className="text-xs text-gray-500 mt-0.5 truncate">{detail}</p>
        )}
      </div>
    </div>
  );
}
