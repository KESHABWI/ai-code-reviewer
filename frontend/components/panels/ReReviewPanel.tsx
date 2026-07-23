"use client";

import { useState } from "react";
import { reviewFile } from "@/lib/api";
import type { FileReview } from "@/lib/types";
import { FileReviewCard } from "../FileReviewCard";
import { Spinner } from "../Spinner";

export function ReReviewPanel({
  projectId,
  files,
}: {
  projectId: string | null;
  files: string[];
}) {
  const [chosen, setChosen] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FileReview | null>(null);

  if (!projectId || files.length === 0) {
    return (
      <p className="rounded-xl border border-dashed border-hairline bg-canvas px-4 py-6 text-center text-[0.85rem] text-faint">
        Analyze a GitHub repo or a .zip above first — then re-review any single file here.
      </p>
    );
  }

  async function run() {
    if (!chosen || !projectId) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await reviewFile(projectId, chosen));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <select
          value={chosen}
          onChange={(e) => setChosen(e.target.value)}
          className="w-full rounded-xl border border-hairline bg-canvas px-4 py-2.5 text-[0.88rem] text-ink focus:border-accent focus:outline-none sm:max-w-sm"
        >
          <option value="">Choose a file…</option>
          {files.map((f) => (
            <option key={f} value={f}>
              {f}
            </option>
          ))}
        </select>
        <button
          onClick={run}
          disabled={!chosen || loading}
          className="flex shrink-0 items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-[0.85rem] font-semibold text-white transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:bg-hairline disabled:text-faint"
        >
          {loading && <Spinner size={14} />}
          Review this file
        </button>
      </div>
      {error && <p className="text-[0.82rem] text-danger">{error}</p>}
      {result && <FileReviewCard review={result} defaultOpen />}
    </div>
  );
}
