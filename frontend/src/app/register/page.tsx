"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { register } from "@/lib/api";
import { setToken, setStoredUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const res = await register(email, password, name);
    setLoading(false);

    if (res.error || !res.data) {
      setError(res.error || "Registration failed");
      return;
    }

    setToken(res.data.access_token);
    setStoredUser(res.data.user);
    router.push("/dashboard");
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <Card className="w-full max-w-md p-8 bg-gray-900 border-gray-800">
        <h1 className="text-2xl font-bold text-white mb-2">
          Start building your business
        </h1>
        <p className="text-gray-400 mb-6">
          Free to start. No credit card required.
        </p>

        {error && (
          <div className="bg-red-900/30 border border-red-800 text-red-300 px-4 py-2 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-gray-400">Name</label>
            <Input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
              required
              className="bg-gray-800 border-gray-700 text-white"
            />
          </div>
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
              minLength={8}
              className="bg-gray-800 border-gray-700 text-white"
            />
          </div>
          <Button
            type="submit"
            className="w-full bg-emerald-500 hover:bg-emerald-600 text-white"
            disabled={loading}
          >
            {loading ? "Creating account..." : "Create Account"}
          </Button>
        </form>

        <p className="text-gray-500 text-sm mt-4 text-center">
          Already have an account?{" "}
          <Link href="/login" className="text-emerald-400 hover:underline">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}
