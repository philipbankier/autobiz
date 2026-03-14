"use client";

import { ArrowLeft, Bot, ClipboardList, Rocket, Timer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface StepConfirmProps {
  name: string;
  slug: string;
  idea: string;
  loading: boolean;
  onBack: () => void;
  onLaunch: () => void;
}

const STEPS_PREVIEW = [
  { icon: Bot, label: "CEO agent analyzes your idea" },
  { icon: ClipboardList, label: "Creates business plan with departments" },
  { icon: Rocket, label: "Sets up GitHub, Vercel, Stripe, email" },
  { icon: Timer, label: "Takes about 90 seconds" },
];

export function StepConfirm({
  name,
  slug,
  idea,
  loading,
  onBack,
  onLaunch,
}: StepConfirmProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-white mb-1">Review & Launch</h2>
        <p className="text-gray-400 text-sm">
          Double-check your details, then let the CEO agent take over.
        </p>
      </div>

      <Card className="p-5 bg-gray-900/50 border-gray-800 space-y-3">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Company</p>
            <p className="text-white font-medium text-lg">{name}</p>
          </div>
          <span className="text-sm text-gray-500 bg-gray-800 px-2 py-0.5 rounded">
            {slug}.autobiz.app
          </span>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Mission</p>
          <p className="text-gray-300 text-sm">{idea}</p>
        </div>
      </Card>

      <Card className="p-5 bg-gray-900/50 border-gray-800">
        <p className="text-sm font-medium text-white mb-4">What happens next</p>
        <div className="space-y-3">
          {STEPS_PREVIEW.map(({ icon: Icon, label }) => (
            <div key={label} className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-lg bg-indigo-950/60 flex items-center justify-center flex-shrink-0">
                <Icon className="h-4 w-4 text-indigo-400" />
              </div>
              <span className="text-sm text-gray-300">{label}</span>
            </div>
          ))}
        </div>
      </Card>

      <div className="flex gap-3">
        <Button variant="outline" onClick={onBack} disabled={loading}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <Button onClick={onLaunch} disabled={loading} size="lg" className="flex-1">
          {loading ? (
            "Creating..."
          ) : (
            <>
              <Rocket className="mr-2 h-4 w-4" />
              Launch Company
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
