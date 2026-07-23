"use client";

import { useState } from "react";
import { reviewDiff } from "@/lib/api";
import type { FileReview } from "@/lib/types";
import { FileReviewCard } from "../FileReviewCard";
import { Spinner } from "../Spinner";

export function DiffPanel() {
  const [filename, setFilename] = useState("example.py");
  const [before, setBefore] = useState("");
  const [after, setAfter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FileReview | null>(null);

  const ready = before.trim().length > 0 && after.trim().length > 0;

  async function run() {
    if (!ready) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await reviewDiff(filename || "snippet.txt", before, after));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <input
        value={filename}
        onChange={(e) => setFilename(e.target.value)}
        placeholder="Filename"
        className="w-full max-w-xs rounded-xl border border-hairline bg-canvas px-4 py-2 text-[0.86rem] text-ink focus:border-accent focus:outline-none"
      />
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1.5 block text-[0.78rem] font-medium text-subink">Before</label>
          <textarea
            value={before}
            onChange={(e) => setBefore(e.target.value)}
            rows={12}
            spellCheck={false}
            className="w-full resize-y rounded-xl border border-hairline bg-canvas px-4 py-3 font-mono text-[0.82rem] leading-relaxed text-ink focus:border-accent focus:outline-none scrollbar-thin"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-[0.78rem] font-medium text-subink">After</label>
          <textarea
            value={after}
            onChange={(e) => setAfter(e.target.value)}
            rows={12}
            spellCheck={false}
            className="w-full resize-y rounded-xl border border-hairline bg-canvas px-4 py-3 font-mono text-[0.82rem] leading-relaxed text-ink focus:border-accent focus:outline-none scrollbar-thin"
          />
        </div>
      </div>
      <button
        onClick={run}
        disabled={!ready || loading}
        className="flex items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-[0.85rem] font-semibold text-white transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:bg-hairline disabled:text-faint"
      >
        {loading && <Spinner size={14} />}
        Review diff
      </button>
      {error && <p className="text-[0.82rem] text-danger">{error}</p>}
      {result && <FileReviewCard review={result} defaultOpen />}
    </div>
  );
}
