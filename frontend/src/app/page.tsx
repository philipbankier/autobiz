import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Zap,
  Bot,
  Clock,
  BarChart3,
  Rocket,
  DollarSign,
  Shield,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

const features = [
  {
    icon: Bot,
    title: "Agent Departments",
    description:
      "Six specialized AI departments — CEO, Developer, Marketing, Sales, Finance, and Support — each with role-specific instructions and autonomous execution.",
  },
  {
    icon: Clock,
    title: "Auto-Scheduling",
    description:
      "3-layer hybrid scheduler: CRON for timed runs, EVENT triggers from webhooks, and CONDITION filters that skip idle departments to save 50–70% on costs.",
  },
  {
    icon: BarChart3,
    title: "Real-Time Dashboard",
    description:
      "Live SSE activity feed, department status cards with budget bars, steering editor, and scheduler controls — all in one view.",
  },
  {
    icon: Rocket,
    title: "One-Click Deploy",
    description:
      "GitHub repo creation, Vercel deployment, and custom domain setup — triggered automatically by your Developer agent.",
  },
  {
    icon: DollarSign,
    title: "Smart Budget Control",
    description:
      "Per-department daily spend limits with model tiering. Opus for strategy, Sonnet for coding, Haiku for quality checks.",
  },
  {
    icon: Shield,
    title: "Quality Gates",
    description:
      "Every agent output is scored by an LLM judge on relevance, quality, completeness, and safety. Failed outputs retry with feedback.",
  },
];

const steps = [
  {
    number: "1",
    title: "Describe",
    description:
      "Tell AutoBiz your business idea — name, mission, and what you want to build.",
  },
  {
    number: "2",
    title: "Launch",
    description:
      "AutoBiz provisions 6 AI departments, creates workspace files, and starts scheduling runs.",
  },
  {
    number: "3",
    title: "Watch",
    description:
      "Monitor progress on the real-time dashboard. Steer priorities. Approve or let agents run free.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-950 text-gray-100">
      {/* Nav */}
      <nav className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-6xl mx-auto flex items-center justify-between h-14 px-6">
          <div className="flex items-center gap-2">
            <Zap className="h-6 w-6 text-purple-500" />
            <span className="text-lg font-bold">AutoBiz</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white">
                Sign In
              </Button>
            </Link>
            <Link href="/register">
              <Button size="sm" className="bg-purple-600 hover:bg-purple-700 text-white">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 -z-10">
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 h-[600px] w-[600px] rounded-full bg-purple-600/10 blur-[128px]" />
            <div className="absolute top-1/2 left-1/4 h-[400px] w-[400px] rounded-full bg-indigo-600/8 blur-[100px]" />
          </div>

          <div className="max-w-6xl mx-auto px-6 pt-28 pb-20 text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-gray-800 bg-gray-900 px-4 py-1.5 text-sm text-gray-400 mb-8">
              <Zap className="h-3.5 w-3.5 text-purple-500" />
              AI-Powered Business Automation
            </div>

            <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold tracking-tight max-w-4xl mx-auto leading-[1.1]">
              Launch AI-Powered Businesses in{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400">
                90 Seconds
              </span>
            </h1>

            <p className="mt-6 text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
              Describe your idea. AutoBiz spins up six autonomous AI departments that
              plan, build, market, and sell — while you sleep. Real-time dashboard.
              Budget controls. Quality gates. All on autopilot.
            </p>

            <div className="flex items-center justify-center gap-4 mt-10">
              <Link href="/register">
                <Button size="lg" className="gap-2 bg-purple-600 hover:bg-purple-700 text-white px-8 h-12 text-base">
                  Start Building Free
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="outline" size="lg" className="border-gray-700 text-gray-300 hover:bg-gray-900 h-12 text-base">
                  Sign In
                </Button>
              </Link>
            </div>

            <p className="mt-4 text-sm text-gray-600">
              No credit card required
            </p>
          </div>
        </section>

        {/* Features Grid */}
        <section className="max-w-6xl mx-auto px-6 py-24">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold">
              Everything your AI company needs
            </h2>
            <p className="mt-3 text-gray-400 max-w-xl mx-auto">
              Six departments. Three scheduling layers. One dashboard.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 hover:border-purple-500/30 transition-colors"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10 mb-4">
                    <Icon className="h-5 w-5 text-purple-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-400 leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </section>

        {/* How It Works */}
        <section className="border-t border-gray-800">
          <div className="max-w-6xl mx-auto px-6 py-24">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold">
                How it works
              </h2>
              <p className="mt-3 text-gray-400">
                Three steps. No configuration headaches.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {steps.map((step) => (
                <div key={step.number} className="text-center">
                  <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-purple-600 text-white text-xl font-bold mb-4">
                    {step.number}
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                  <p className="text-gray-400 text-sm leading-relaxed">
                    {step.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Benchmark */}
        <section className="border-t border-gray-800">
          <div className="max-w-4xl mx-auto px-6 py-24 text-center">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Battle-tested
            </h2>
            <p className="text-gray-400 mb-10">
              17 end-to-end tests. 72 seconds. Every feature verified.
            </p>

            <div className="grid grid-cols-3 gap-6">
              <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
                <div className="text-3xl font-bold text-purple-400">17/17</div>
                <div className="text-sm text-gray-500 mt-1">Tests passing</div>
              </div>
              <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
                <div className="text-3xl font-bold text-purple-400">20s</div>
                <div className="text-sm text-gray-500 mt-1">Company creation</div>
              </div>
              <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
                <div className="text-3xl font-bold text-purple-400">72s</div>
                <div className="text-sm text-gray-500 mt-1">Full E2E suite</div>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section className="border-t border-gray-800">
          <div className="max-w-4xl mx-auto px-6 py-24 text-center">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Pricing
            </h2>
            <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-10 max-w-md mx-auto">
              <div className="text-sm text-purple-400 font-medium uppercase tracking-wider mb-2">
                Coming Soon
              </div>
              <div className="text-4xl font-bold mb-2">Early Access</div>
              <p className="text-gray-400 mb-6">
                Free while in beta. Usage-based pricing launching soon.
              </p>
              <Link href="/register">
                <Button className="w-full bg-purple-600 hover:bg-purple-700 text-white gap-2">
                  Get Early Access
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <div className="mt-6 space-y-2 text-left">
                {[
                  "6 AI departments included",
                  "Real-time dashboard",
                  "Unlimited companies",
                  "Deploy pipeline",
                ].map((item) => (
                  <div key={item} className="flex items-center gap-2 text-sm text-gray-400">
                    <CheckCircle2 className="h-4 w-4 text-purple-500 shrink-0" />
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="border-t border-gray-800">
          <div className="max-w-6xl mx-auto px-6 py-24 text-center">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Ready to automate your business?
            </h2>
            <p className="text-gray-400 mb-8 max-w-lg mx-auto">
              Create your first AI company in under two minutes. No credit card required.
            </p>
            <Link href="/register">
              <Button size="lg" className="gap-2 bg-purple-600 hover:bg-purple-700 text-white px-8 h-12 text-base">
                Get Started Free
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-purple-500" />
            <span className="font-medium text-gray-400">AutoBiz</span>
          </div>
          <div className="flex items-center gap-6">
            <Link href="/login" className="hover:text-gray-300 transition-colors">
              Sign In
            </Link>
            <Link href="/register" className="hover:text-gray-300 transition-colors">
              Get Started
            </Link>
          </div>
          <p>Built with AI, for AI-powered businesses.</p>
        </div>
      </footer>
    </div>
  );
}
