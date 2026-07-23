import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Codelight — AI Code Reviewer",
  description:
    "Instant, PR-style code review. Paste a GitHub link or drop in a file — get a verdict, a summary, and line-by-line feedback in seconds.",
  icons: {
    icon: "/logo/favicon.svg",
  },
};

export const viewport: Viewport = {
  themeColor: "#fbfbfd",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-text antialiased">{children}</body>
    </html>
  );
}
