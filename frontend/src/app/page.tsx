import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Zap, Bot, BarChart3, Shield, ArrowRight } from "lucide-react";

const features = [
  {
    icon: Bot,
    title: "Autonomous Departments",
    description:
      "Marketing, Sales, Support, Engineering -- each powered by specialized AI agents that work 24/7.",
  },
  {
    icon: BarChart3,
    title: "Real-time Insights",
    description:
      "Monitor agent activity, costs, and performance across all departments from a single dashboard.",
  },
  {
    icon: Shield,
    title: "You Stay in Control",
    description:
      "Set autonomy levels per department. From fully autonomous to human-approval-required.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Nav */}
      <nav className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-6xl mx-auto flex items-center justify-between h-14 px-6">
          <div className="flex items-center gap-2">
            <Zap className="h-6 w-6 text-primary" />
            <span className="text-lg font-bold">AutoBiz</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link href="/register">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <main className="flex-1">
        <section className="relative overflow-hidden">
          {/* Gradient background */}
          <div className="absolute inset-0 -z-10">
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 h-[600px] w-[600px] rounded-full bg-primary/10 blur-[128px]" />
          </div>

          <div className="max-w-6xl mx-auto px-6 pt-24 pb-16 text-center">
            <div className="inline-flex items-center gap-2 rounded-full border bg-card px-4 py-1.5 text-sm text-muted-foreground mb-8">
              <Zap className="h-3.5 w-3.5 text-primary" />
              AI-Powered Business Automation
            </div>

            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight max-w-3xl mx-auto leading-[1.1]">
              Your AI company that works{" "}
              <span className="text-primary">while you sleep</span>
            </h1>

            <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto">
              Launch autonomous AI departments -- marketing, sales, support, and more.
              Each department runs independently, reports back to you, and scales
              without limits.
            </p>

            <div className="flex items-center justify-center gap-4 mt-10">
              <Link href="/register">
                <Button size="lg" className="gap-2">
                  Start Building
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="outline" size="lg">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="max-w-6xl mx-auto px-6 py-24">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold">
              Everything runs on autopilot
            </h2>
            <p className="mt-3 text-muted-foreground max-w-xl mx-auto">
              Configure once, let AI handle the rest. Monitor and adjust whenever you want.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="rounded-xl border bg-card p-6 hover:border-primary/50 transition-colors"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 mb-4">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </section>

        {/* CTA */}
        <section className="border-t">
          <div className="max-w-6xl mx-auto px-6 py-24 text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to automate?</h2>
            <p className="text-muted-foreground mb-8 max-w-lg mx-auto">
              Create your first AI company in minutes. No credit card required.
            </p>
            <Link href="/register">
              <Button size="lg" className="gap-2">
                Get Started Free
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-primary" />
            AutoBiz
          </div>
          <p>Built with AI, for AI-powered businesses.</p>
        </div>
      </footer>
    </div>
  );
}
