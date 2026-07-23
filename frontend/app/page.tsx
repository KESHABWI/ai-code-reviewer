"use client";

import { useState } from "react";
import { Header } from "@/components/Header";
import { AnalyzeCard } from "@/components/AnalyzeCard";
import { ResultsPanel } from "@/components/ResultsPanel";
import { SegmentedControl } from "@/components/SegmentedControl";
import { ReReviewPanel } from "@/components/panels/ReReviewPanel";
import { DiffPanel } from "@/components/panels/DiffPanel";
import { HistoryPanel } from "@/components/panels/HistoryPanel";
import { analyzeGithub, analyzeUpload, ApiError } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";

type Tab = "rereview" | "diff" | "history";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [tab, setTab] = useState<Tab>("rereview");

  const projectId = result?.project_id ?? null;
  const projectFiles = result?.project_review?.files.map((f) => f.path) ?? [];

  async function runAnalysis(task: () => Promise<AnalyzeResponse>) {
    setLoading(true);
    setError(null);
    try {
      setResult(await task());
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : "Couldn't reach the review engine. Check that the backend is running."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-canvas">
      <Header />

      {/* Hero */}
      <section className="mx-auto max-w-5xl px-5 pb-10 pt-16 text-center sm:px-8 sm:pt-24">
        <h1 className="animate-fadeUp font-display text-[2.5rem] font-semibold leading-[1.08] tracking-[-0.03em] text-ink sm:text-[3.4rem]">
          Every commit,
          <br />
          <span className="bg-gradient-to-r from-[#0071e3] to-[#5e5ce6] bg-clip-text text-transparent">
            reviewed like a teammate did it.
          </span>
        </h1>
        <p
          className="animate-fadeUp mx-auto mt-5 max-w-xl text-[1.05rem] leading-relaxed text-subink"
          style={{ animationDelay: "80ms" }}
        >
          Paste a GitHub link, or drop in a .zip or a single file. Get a verdict, a plain-English
          summary, and line-by-line notes — in the time it takes to get coffee.
        </p>
      </section>

      {/* Analyze */}
      <section className="mx-auto max-w-3xl px-5 sm:px-8">
        <div className="animate-fadeUp" style={{ animationDelay: "140ms" }}>
          <AnalyzeCard
            loading={loading}
            onSubmitLink={(url) => runAnalysis(() => analyzeGithub(url))}
            onSubmitFile={(file) => runAnalysis(() => analyzeUpload(file))}
          />
        </div>

        {error && (
          <p className="animate-fadeUp mt-4 rounded-xl border border-danger/25 bg-[#fde8e7] px-4 py-3 text-[0.85rem] text-[#c0271d]">
            {error}
          </p>
        )}
      </section>

      {/* Results */}
      {result && (
        <section className="mx-auto max-w-3xl px-5 pt-8 sm:px-8">
          <ResultsPanel result={result} />
        </section>
      )}

      {/* Secondary tools */}
      <section className="mx-auto max-w-3xl px-5 py-16 sm:px-8">
        <div className="mb-6 flex flex-col gap-4 border-t border-hairline/70 pt-10 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="font-display text-[1.15rem] font-semibold tracking-[-0.01em] text-ink">
            More tools
          </h2>
          <SegmentedControl<Tab>
            value={tab}
            onChange={setTab}
            options={[
              { value: "rereview", label: "Re-review a file" },
              { value: "diff", label: "Diff review" },
              { value: "history", label: "History" },
            ]}
          />
        </div>

        {tab === "rereview" && <ReReviewPanel projectId={projectId} files={projectFiles} />}
        {tab === "diff" && <DiffPanel />}
        {tab === "history" && <HistoryPanel />}
      </section>

      <footer className="border-t border-hairline/70 py-8 text-center text-[0.78rem] text-faint">
        Codelight · powered by Ollama + code-index-mcp
      </footer>
    </main>
  );
}
