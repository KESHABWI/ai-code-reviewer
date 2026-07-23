import type { AnalyzeResponse } from "@/lib/types";
import { VerdictPill } from "./Badges";
import { FileReviewCard } from "./FileReviewCard";
import { AlreadyAnalyzedBanner } from "./AlreadyAnalyzedBanner";

export function ResultsPanel({ result }: { result: AnalyzeResponse }) {
  return (
    <div className="animate-fadeUp space-y-5">
      {result.already_analyzed ? (
        <AlreadyAnalyzedBanner sourceLabel={result.source_label} analyzedAt={result.analyzed_at} />
      ) : (
        <div className="flex items-center gap-2 text-[0.85rem] font-medium text-[#1e7a37]">
          <svg className="h-4 w-4" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="8.5" stroke="currentColor" strokeWidth="1.6" />
            <path d="M6.5 10.2 9 12.7l4.5-5.4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Analyzed <code className="font-mono text-ink">{result.source_label}</code> just now.
        </div>
      )}

      {result.project_review && (
        <>
          <div className="rounded-2xl border border-hairline/70 bg-surface p-5 shadow-card sm:p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="font-display text-[1.05rem] font-semibold tracking-[-0.01em] text-ink">
                Overall verdict
              </h3>
              <VerdictPill verdict={result.project_review.overall_verdict} />
            </div>
            <p className="mt-2 text-[0.85rem] leading-relaxed text-subink">
              {result.project_review.overall_justification}
            </p>
            <p className="mt-3 text-[0.9rem] leading-relaxed text-ink">
              {result.project_review.overall_summary}
            </p>
          </div>

          <div className="space-y-3">
            <h3 className="font-display text-[0.95rem] font-semibold tracking-[-0.01em] text-ink">
              Per-file reviews ({result.project_review.files.length})
            </h3>
            <div className="space-y-3">
              {result.project_review.files.map((fr) => (
                <FileReviewCard key={fr.path} review={fr} />
              ))}
            </div>
          </div>
        </>
      )}

      {result.file_review && (
        <FileReviewCard review={result.file_review} defaultOpen />
      )}
    </div>
  );
}
