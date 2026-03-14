"use client";

import { useState } from "react";
import { Lightbulb, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";

const EXAMPLE_IDEAS = [
  "AI social media scheduler that auto-generates and posts content for small businesses",
  "Local bakery delivery service connecting neighborhood bakeries with customers",
  "SaaS invoice and expense tracking tool built for freelancers and solopreneurs",
];

interface StepIdeaProps {
  idea: string;
  name: string;
  slug: string;
  onIdeaChange: (idea: string) => void;
  onNameChange: (name: string) => void;
  onSlugChange: (slug: string) => void;
  onNext: () => void;
}

function generateNameFromIdea(idea: string): string {
  const words = idea
    .replace(/[^a-zA-Z0-9\s]/g, "")
    .split(/\s+/)
    .filter((w) => w.length > 2)
    .slice(0, 3);
  if (words.length === 0) return "";
  return words.map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join("");
}

function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function StepIdea({
  idea,
  name,
  slug,
  onIdeaChange,
  onNameChange,
  onSlugChange,
  onNext,
}: StepIdeaProps) {
  const [nameManuallyEdited, setNameManuallyEdited] = useState(false);

  function handleIdeaChange(value: string) {
    onIdeaChange(value);
    if (!nameManuallyEdited && value.length > 10) {
      const suggested = generateNameFromIdea(value);
      onNameChange(suggested);
      onSlugChange(slugify(suggested));
    }
  }

  function handleNameChange(value: string) {
    setNameManuallyEdited(true);
    onNameChange(value);
    onSlugChange(slugify(value));
  }

  function handleExampleClick(example: string) {
    handleIdeaChange(example);
    setNameManuallyEdited(false);
    const suggested = generateNameFromIdea(example);
    onNameChange(suggested);
    onSlugChange(slugify(suggested));
  }

  const isValid = idea.trim().length >= 10 && name.trim().length > 0 && slug.trim().length > 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-white mb-1">Describe Your Business</h2>
        <p className="text-gray-400 text-sm">
          Tell us about your business idea in a couple of sentences. Our CEO agent will take it from there.
        </p>
      </div>

      <div>
        <Textarea
          value={idea}
          onChange={(e) => handleIdeaChange(e.target.value)}
          placeholder="Describe your business idea in 2-3 sentences..."
          rows={4}
          className="bg-gray-800 border-gray-700 text-white text-base"
        />
        <p className="text-gray-600 text-xs mt-1">
          Be specific about what your business does, who it serves, and what makes it unique.
        </p>
      </div>

      <div>
        <p className="text-xs text-gray-500 mb-2 flex items-center gap-1.5">
          <Lightbulb className="h-3.5 w-3.5" />
          Try an example
        </p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_IDEAS.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => handleExampleClick(example)}
              className="text-xs px-3 py-1.5 rounded-full bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200 border border-gray-700 transition-colors"
            >
              {example.length > 50 ? example.slice(0, 50) + "..." : example}
            </button>
          ))}
        </div>
      </div>

      <Card className="p-5 bg-gray-900/50 border-gray-800 space-y-4">
        <div>
          <label className="text-sm text-gray-400 mb-1 block">Company Name</label>
          <Input
            value={name}
            onChange={(e) => handleNameChange(e.target.value)}
            placeholder="MyCompany"
            className="bg-gray-800 border-gray-700 text-white"
          />
        </div>
        <div>
          <label className="text-sm text-gray-400 mb-1 block">Slug</label>
          <div className="flex items-center gap-2">
            <Input
              value={slug}
              onChange={(e) =>
                onSlugChange(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""))
              }
              placeholder="mycompany"
              className="bg-gray-800 border-gray-700 text-white"
            />
            <span className="text-gray-500 text-sm whitespace-nowrap">.autobiz.app</span>
          </div>
        </div>
      </Card>

      <div className="flex justify-end">
        <Button onClick={onNext} disabled={!isValid} size="lg">
          Next
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
