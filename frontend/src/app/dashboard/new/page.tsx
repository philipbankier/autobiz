"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createCompany } from "@/lib/api";
import { StepIdea } from "@/components/onboarding/step-idea";
import { StepConfirm } from "@/components/onboarding/step-confirm";
import { StepProgress } from "@/components/onboarding/step-progress";

type WizardStep = "idea" | "confirm" | "progress";

export default function NewCompanyPage() {
  const router = useRouter();
  const [step, setStep] = useState<WizardStep>("idea");
  const [idea, setIdea] = useState("");
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [companyId, setCompanyId] = useState<string | null>(null);

  async function handleLaunch() {
    setError("");
    setLoading(true);

    const res = await createCompany(name, idea, slug);
    setLoading(false);

    if (res.error || !res.data) {
      setError(res.error || "Failed to create company");
      return;
    }

    setCompanyId(res.data.id);
    setStep("progress");
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-8">
        {(["idea", "confirm", "progress"] as const).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                s === step
                  ? "w-8 bg-indigo-500"
                  : (["idea", "confirm", "progress"].indexOf(s) <
                      ["idea", "confirm", "progress"].indexOf(step))
                    ? "w-8 bg-indigo-500/40"
                    : "w-2 bg-gray-700"
              }`}
            />
            {i < 2 && <div className="w-1" />}
          </div>
        ))}
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-800 text-red-300 px-4 py-2 rounded-lg mb-6 text-sm">
          {error}
        </div>
      )}

      {step === "idea" && (
        <StepIdea
          idea={idea}
          name={name}
          slug={slug}
          onIdeaChange={setIdea}
          onNameChange={setName}
          onSlugChange={setSlug}
          onNext={() => setStep("confirm")}
        />
      )}

      {step === "confirm" && (
        <StepConfirm
          name={name}
          slug={slug}
          idea={idea}
          loading={loading}
          onBack={() => setStep("idea")}
          onLaunch={handleLaunch}
        />
      )}

      {step === "progress" && companyId && (
        <StepProgress
          companyId={companyId}
          onComplete={() => router.push(`/dashboard/${companyId}`)}
        />
      )}
    </div>
  );
}
