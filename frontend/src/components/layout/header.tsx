"use client";

import { useRouter } from "next/navigation";
import { Avatar } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { logout, getStoredUser } from "@/lib/auth";
import { LogOut, User, Zap } from "lucide-react";

export function Header() {
  const router = useRouter();
  const user = getStoredUser();

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-6">
      <div className="flex items-center gap-2 md:hidden">
        <Zap className="h-5 w-5 text-primary" />
        <span className="font-bold">AutoBiz</span>
      </div>
      <div className="hidden md:block" />
      <DropdownMenu>
        <DropdownMenuTrigger className="flex items-center gap-2 rounded-lg px-2 py-1 hover:bg-accent transition-colors">
          <Avatar
            fallback={user?.name?.charAt(0).toUpperCase() || "U"}
            className="h-8 w-8"
          />
          <span className="text-sm hidden sm:inline">{user?.name || "User"}</span>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <div className="px-2 py-1.5">
            <p className="text-sm font-medium">{user?.name || "User"}</p>
            <p className="text-xs text-muted-foreground">{user?.email || ""}</p>
          </div>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => router.push("/dashboard")}>
            <User className="mr-2 h-4 w-4" />
            Dashboard
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={logout}>
            <LogOut className="mr-2 h-4 w-4" />
            Log out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
