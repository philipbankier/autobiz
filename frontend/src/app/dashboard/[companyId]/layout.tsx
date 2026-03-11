"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";

const tabs = [
  { label: "Overview", path: "" },
  { label: "Activity", path: "/activity" },
  { label: "Chat", path: "/chat" },
  { label: "Tasks", path: "/tasks" },
  { label: "Settings", path: "/settings" },
];

export default function CompanyLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const pathname = usePathname();
  const companyId = params.companyId as string;
  const basePath = `/dashboard/${companyId}`;

  return (
    <div>
      <nav className="flex gap-1 mb-6 border-b border-gray-800 pb-2">
        {tabs.map((tab) => {
          const href = `${basePath}${tab.path}`;
          const isActive = pathname === href || (tab.path === "" && pathname === basePath);
          return (
            <Link
              key={tab.path}
              href={href}
              className={`px-4 py-2 rounded-t text-sm transition-colors ${
                isActive
                  ? "text-white bg-gray-800 font-medium"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>
      {children}
    </div>
  );
}
