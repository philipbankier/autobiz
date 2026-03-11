"use client";

import Link from "next/link";
import { usePathname, useParams } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Activity,
  MessageSquare,
  ListTodo,
  Settings,
} from "lucide-react";

const tabs = [
  { href: "", label: "Overview", icon: LayoutDashboard },
  { href: "/activity", label: "Activity", icon: Activity },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/tasks", label: "Tasks", icon: ListTodo },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function CompanyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const params = useParams();
  const basePath = `/dashboard/${params.companyId}`;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">NexGen AI Solutions</h1>
        <p className="text-sm text-muted-foreground">/nexgen-ai-solutions</p>
      </div>

      <nav className="flex gap-1 border-b mb-6 overflow-x-auto">
        {tabs.map((tab) => {
          const href = `${basePath}${tab.href}`;
          const isActive =
            tab.href === ""
              ? pathname === basePath
              : pathname === href;
          const Icon = tab.icon;

          return (
            <Link
              key={tab.href}
              href={href}
              className={cn(
                "flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors whitespace-nowrap",
                isActive
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
              )}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </Link>
          );
        })}
      </nav>

      {children}
    </div>
  );
}
