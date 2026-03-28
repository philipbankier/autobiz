import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AutoBiz — Describe your idea. Get a live business.",
  description:
    "Turn your business idea into a real company with AI. Website, payments, marketing — all handled. No coding required.",
  openGraph: {
    title: "AutoBiz — Describe your idea. Get a live business.",
    description:
      "Turn your business idea into a real company with AI. Website, payments, marketing — all handled. No coding required.",
    siteName: "AutoBiz",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AutoBiz — Describe your idea. Get a live business.",
    description:
      "Turn your business idea into a real company with AI. Website, payments, marketing — all handled. No coding required.",
  },
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
  other: {
    "theme-color": "#10b981",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <meta name="theme-color" content="#10b981" />
      </head>
      <body className={inter.className}>{children}</body>
    </html>
  );
}
