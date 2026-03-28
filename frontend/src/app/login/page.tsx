"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login } from "@/lib/api";
import { setToken, setStoredUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const res = await login(email, password);
    setLoading(false);

    if (res.error || !res.data) {
      setError(res.error || "Login failed");
      return;
    }

    setToken(res.data.access_token);
    setStoredUser(res.data.user);
    router.push("/dashboard");
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <Card className="w-full max-w-md p-8 bg-gray-900 border-gray-800">
        <h1 className="text-2xl font-bold text-white mb-2">Welcome back</h1>
        <p className="text-gray-400 mb-6">
          Sign in to manage your businesses
        </p>

        {error && (
          <div className="bg-red-900/30 border border-red-800 text-red-300 px-4 py-2 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-gray-400">Email</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="bg-gray-800 border-gray-700 text-white"
            />
          </div>
          <div>
            <label className="text-sm text-gray-400">Password</label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="bg-gray-800 border-gray-700 text-white"
            />
          </div>
          <Button
            type="submit"
            className="w-full bg-emerald-500 hover:bg-emerald-600 text-white"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign In"}
          </Button>
        </form>

        <p className="text-gray-500 text-sm mt-4 text-center">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-emerald-400 hover:underline">
            Register
          </Link>
        </p>
      </Card>
    </div>
  );
}
