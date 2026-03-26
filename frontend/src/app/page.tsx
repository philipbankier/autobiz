import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Zap,
  ArrowRight,
  CheckCircle2,
  Lightbulb,
  Users,
  BarChart3,
  Crown,
  Code2,
  Megaphone,
  Coins,
  Landmark,
  HeadphonesIcon,
  Shield,
  DollarSign,
  Clock,
} from "lucide-react";

const departments = [
  {
    icon: Crown,
    name: "CEO",
    description: "Sets strategy, coordinates teams, and keeps everything on track.",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
  },
  {
    icon: Code2,
    name: "Developer",
    description: "Builds your product, deploys code, and manages your tech stack.",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  {
    icon: Megaphone,
    name: "Marketing",
    description: "Creates content, runs campaigns, and grows your audience.",
    color: "text-pink-400",
    bg: "bg-pink-500/10",
  },
  {
    icon: Coins,
    name: "Sales",
    description: "Finds leads, handles outreach, and closes deals.",
    color: "text-green-400",
    bg: "bg-green-500/10",
  },
  {
    icon: Landmark,
    name: "Finance",
    description: "Tracks spending, manages budgets, and keeps the books clean.",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
  },
  {
    icon: HeadphonesIcon,
    name: "Support",
    description: "Answers questions, resolves issues, and keeps customers happy.",
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
  },
];

const features = [
  {
    icon: BarChart3,
    title: "Watch it happen live",
    description:
      "A real-time dashboard shows what each department is working on, what they've accomplished, and what's coming next.",
  },
  {
    icon: DollarSign,
    title: "Stay in control of costs",
    description:
      "Set daily spending limits for each department. Your AI team works smart within the budget you choose.",
  },
  {
    icon: Shield,
    title: "Quality you can trust",
    description:
      "Every piece of work is automatically reviewed before it goes live. Nothing ships unless it meets the bar.",
  },
  {
    icon: Clock,
    title: "Runs while you sleep",
    description:
      "Your departments work around the clock on their own schedule. Check in when you want, or let them handle it.",
  },
];

const steps = [
  {
    number: "1",
    icon: Lightbulb,
    title: "Describe your idea",
    description:
      "Tell us what your business does, who it's for, and what you want to build. That's all we need.",
  },
  {
    number: "2",
    icon: Users,
    title: "Meet your AI team",
    description:
      "In about 90 seconds, six departments spin up and start working on your business.",
  },
  {
    number: "3",
    icon: BarChart3,
    title: "Watch and steer",
    description:
      "Follow progress on your dashboard. Jump in to guide priorities, or sit back and let them run.",
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
              Free during beta
            </div>

            <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold tracking-tight max-w-4xl mx-auto leading-[1.1]">
              Describe your idea.{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400">
                We build your AI company.
              </span>
            </h1>

            <p className="mt-6 text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
              Tell us your business idea and get a full AI-powered team in 90 seconds.
              Six departments that plan, build, market, and sell — working for you around the clock.
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

        {/* AI Team */}
        <section className="max-w-6xl mx-auto px-6 py-24">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold">
              Your AI team, ready to work
            </h2>
            <p className="mt-3 text-gray-400 max-w-xl mx-auto">
              Six departments that handle the day-to-day so you can focus on the big picture.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {departments.map((dept) => {
              const Icon = dept.icon;
              return (
                <div
                  key={dept.name}
                  className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 hover:border-purple-500/30 transition-colors"
                >
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${dept.bg} mb-4`}>
                    <Icon className={`h-5 w-5 ${dept.color}`} />
                  </div>
                  <h3 className="text-lg font-semibold mb-1">{dept.name}</h3>
                  <p className="text-sm text-gray-400 leading-relaxed">
                    {dept.description}
                  </p>
                </div>
              );
            })}
          </div>
        </section>

        {/* Features */}
        <section className="border-t border-gray-800">
          <div className="max-w-6xl mx-auto px-6 py-24">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold">
                You stay in charge
              </h2>
              <p className="mt-3 text-gray-400 max-w-xl mx-auto">
                Your AI team is autonomous, but you always have the final say.
              </p>
            </div>

            <div className="grid sm:grid-cols-2 gap-6">
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
                From idea to running business in three steps.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {steps.map((step) => {
                const Icon = step.icon;
                return (
                  <div key={step.number} className="text-center">
                    <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-purple-600 text-white text-xl font-bold mb-4">
                      {step.number}
                    </div>
                    <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                    <p className="text-gray-400 text-sm leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section className="border-t border-gray-800">
          <div className="max-w-4xl mx-auto px-6 py-24 text-center">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Free while we're in beta
            </h2>
            <p className="text-gray-400 mb-10 max-w-lg mx-auto">
              Try AutoBiz with no limits and no credit card. We'll introduce simple pricing once we're out of beta.
            </p>

            <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-10 max-w-md mx-auto">
              <div className="text-sm text-purple-400 font-medium uppercase tracking-wider mb-2">
                Beta
              </div>
              <div className="text-4xl font-bold mb-2">$0</div>
              <p className="text-gray-400 mb-6">
                Everything included. No strings attached.
              </p>
              <Link href="/register">
                <Button className="w-full bg-purple-600 hover:bg-purple-700 text-white gap-2">
                  Get Started Free
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <div className="mt-6 space-y-2 text-left">
                {[
                  "6 AI departments",
                  "Real-time dashboard",
                  "Unlimited companies",
                  "Budget controls",
                  "Quality gates",
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
              Your next business is one idea away
            </h2>
            <p className="text-gray-400 mb-8 max-w-lg mx-auto">
              Describe what you want to build. Your AI team handles the rest.
            </p>
            <Link href="/register">
              <Button size="lg" className="gap-2 bg-purple-600 hover:bg-purple-700 text-white px-8 h-12 text-base">
                Start Building Free
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
          <p>Your AI-powered business team.</p>
        </div>
      </footer>
    </div>
  );
}
