import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Zap } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-950 text-gray-100 px-6">
      <Zap className="h-12 w-12 text-emerald-500 mb-6" />
      <h1 className="text-4xl font-bold mb-2">This page doesn&apos;t exist</h1>
      <p className="text-gray-400 mb-8">
        The page you&apos;re looking for couldn&apos;t be found.
      </p>
      <Link href="/">
        <Button className="bg-emerald-500 hover:bg-emerald-600 text-white">
          Back to Home
        </Button>
      </Link>
    </div>
  );
}
