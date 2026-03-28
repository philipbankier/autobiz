import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Zap,
  ArrowRight,
  Globe,
  CreditCard,
  FileText,
  Megaphone,
  Bot,
  Download,
  Check,
} from "lucide-react";

const outcomes = [
  {
    icon: Globe,
    title: "A real website",
    description: "Professional site deployed and ready to share.",
  },
  {
    icon: CreditCard,
    title: "Payments from day one",
    description: "Stripe checkout configured and tested.",
  },
  {
    icon: FileText,
    title: "A business plan",
    description: "Strategy, pricing, target audience — all figured out.",
  },
  {
    icon: Megaphone,
    title: "Marketing on autopilot",
    description: "Social content, launch copy, SEO basics.",
  },
  {
    icon: Bot,
    title: "Ongoing AI operations",
    description:
      "Your AI team keeps working: updating content, monitoring, improving.",
  },
  {
    icon: Download,
    title: "Full ownership",
    description: "Everything is yours. Export anytime. No lock-in.",
  },
];

const steps = [
  {
    number: "1",
    title: "Tell us your idea",
    description:
      "Describe your business in a sentence or two. That's all we need.",
  },
  {
    number: "2",
    title: "Watch it come together",
    description:
      "Our AI team builds your website, sets up payments, creates your brand, and writes your marketing materials.",
  },
  {
    number: "3",
    title: "Launch and grow",
    description:
      "Review everything, make changes through simple chat, and go live. Your AI team keeps working in the background.",
  },
];

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "",
    description: "See your business plan and website preview",
    features: ["Business plan generation", "Website preview", "Brand strategy"],
    cta: "Start Free",
    highlighted: false,
  },
  {
    name: "Launch",
    price: "$9",
    period: "/mo",
    description: "Live website, Stripe payments, ongoing AI operations",
    features: [
      "Live deployed website",
      "Stripe payment processing",
      "AI operations team",
      "Marketing materials",
      "Email support",
    ],
    cta: "Get Started",
    highlighted: true,
  },
  {
    name: "Growth",
    price: "$9",
    period: "/mo",
    description: "Multiple businesses, custom domain, priority support",
    features: [
      "Everything in Launch",
      "Multiple businesses",
      "Custom domain",
      "Priority support",
      "Advanced analytics",
    ],
    cta: "Get Started",
    highlighted: false,
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-950 text-gray-100">
      {/* Nav */}
      <nav className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-6xl mx-auto flex items-center justify-between h-14 px-6">
          <div className="flex items-center gap-2">
            <Zap className="h-6 w-6 text-emerald-500" />
            <span className="text-lg font-bold">AutoBiz</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white"
              >
                Sign In
              </Button>
            </Link>
            <Link href="/register">
              <Button
                size="sm"
                className="bg-emerald-500 hover:bg-emerald-600 text-white"
              >
                Start Free
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 -z-10">
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 h-[600px] w-[600px] rounded-full bg-emerald-600/10 blur-[128px]" />
            <div className="absolute top-1/2 left-1/4 h-[400px] w-[400px] rounded-full bg-teal-600/8 blur-[100px]" />
          </div>

          <div className="max-w-6xl mx-auto px-6 pt-28 pb-20 text-center">
            <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold tracking-tight max-w-4xl mx-auto leading-[1.1]">
              Describe your idea.{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-400">
                Get a live business.
              </span>
            </h1>

            <p className="mt-6 text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
              AutoBiz turns your business idea into a real company — with a
              website, payment processing, marketing, and an AI team that keeps
              working after launch. No coding required.
            </p>

            <div className="flex items-center justify-center gap-4 mt-10">
              <Link href="/register">
                <Button
                  size="lg"
                  className="gap-2 bg-emerald-500 hover:bg-emerald-600 text-white px-8 h-12 text-base"
                >
                  Start Free
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <a href="#how-it-works">
                <Button
                  variant="outline"
                  size="lg"
                  className="border-gray-700 text-gray-300 hover:bg-gray-900 h-12 text-base"
                >
                  See how it works
                </Button>
              </a>
            </div>

            <p className="mt-4 text-sm text-gray-600">
              No credit card required
            </p>
          </div>
        </section>

        {/* What You Get */}
        <section className="max-w-6xl mx-auto px-6 py-24">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold">What you get</h2>
            <p className="mt-3 text-gray-400 max-w-xl mx-auto">
              Everything you need to go from idea to revenue.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {outcomes.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.title}
                  className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 hover:border-emerald-500/30 transition-colors"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 mb-4">
                    <Icon className="h-5 w-5 text-emerald-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-1">{item.title}</h3>
                  <p className="text-sm text-gray-400 leading-relaxed">
                    {item.description}
                  </p>
                </div>
              );
            })}
          </div>
        </section>

        {/* How It Works */}
        <section id="how-it-works" className="border-t border-gray-800">
          <div className="max-w-6xl mx-auto px-6 py-24">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold">How it works</h2>
              <p className="mt-3 text-gray-400">
                Three steps. No technical skills needed.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {steps.map((step) => (
                <div key={step.number} className="text-center">
                  <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500 text-white text-xl font-bold mb-4">
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

        {/* Pricing */}
        <section className="border-t border-gray-800">
          <div className="max-w-5xl mx-auto px-6 py-24">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold">
                Simple pricing
              </h2>
              <p className="mt-3 text-gray-400 max-w-lg mx-auto">
                Start free. Upgrade when you're ready to go live.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              {plans.map((plan) => (
                <div
                  key={plan.name}
                  className={`rounded-xl border p-8 ${
                    plan.highlighted
                      ? "border-emerald-500 bg-gray-900"
                      : "border-gray-800 bg-gray-900/50"
                  }`}
                >
                  {plan.highlighted && (
                    <div className="text-xs font-medium text-emerald-400 uppercase tracking-wider mb-2">
                      Most Popular
                    </div>
                  )}
                  <h3 className="text-xl font-bold mb-1">{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mb-2">
                    <span className="text-3xl font-bold">{plan.price}</span>
                    {plan.period && (
                      <span className="text-gray-500">{plan.period}</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-400 mb-6">
                    {plan.description}
                  </p>
                  <Link href="/register">
                    <Button
                      className={`w-full mb-6 ${
                        plan.highlighted
                          ? "bg-emerald-500 hover:bg-emerald-600 text-white"
                          : "bg-gray-800 hover:bg-gray-700 text-white"
                      }`}
                    >
                      {plan.cta}
                    </Button>
                  </Link>
                  <div className="space-y-2">
                    {plan.features.map((feature) => (
                      <div
                        key={feature}
                        className="flex items-center gap-2 text-sm text-gray-400"
                      >
                        <Check className="h-4 w-4 text-emerald-500 shrink-0" />
                        {feature}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Social Proof */}
        <section className="border-t border-gray-800">
          <div className="max-w-6xl mx-auto px-6 py-16 text-center">
            <p className="text-lg text-gray-500">
              Join founders who launched with AutoBiz
            </p>
          </div>
        </section>

        {/* CTA */}
        <section className="border-t border-gray-800">
          <div className="max-w-6xl mx-auto px-6 py-24 text-center">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Your next business is one idea away
            </h2>
            <p className="text-gray-400 mb-8 max-w-lg mx-auto">
              Describe what you want to build. We handle the rest.
            </p>
            <Link href="/register">
              <Button
                size="lg"
                className="gap-2 bg-emerald-500 hover:bg-emerald-600 text-white px-8 h-12 text-base"
              >
                Start Free
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
            <Zap className="h-4 w-4 text-emerald-500" />
            <span className="font-medium text-gray-400">AutoBiz</span>
          </div>
          <div className="flex items-center gap-6">
            <Link
              href="/register"
              className="hover:text-gray-300 transition-colors"
            >
              Register
            </Link>
            <Link
              href="/login"
              className="hover:text-gray-300 transition-colors"
            >
              Sign In
            </Link>
            <a href="#" className="hover:text-gray-300 transition-colors">
              Terms
            </a>
            <a href="#" className="hover:text-gray-300 transition-colors">
              Privacy
            </a>
          </div>
          <p>&copy; {new Date().getFullYear()} AutoBiz</p>
        </div>
      </footer>
    </div>
  );
}
