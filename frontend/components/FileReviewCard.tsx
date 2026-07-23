"use client";

import { useState } from "react";
import type { FileReview } from "@/lib/types";
import { VerdictPill, SeverityTag } from "./Badges";

export function FileReviewCard({
  review,
  defaultOpen = false,
}: {
  review: FileReview;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const issueCount = review.issues?.length ?? 0;

  return (
    <div className="rounded-2xl border border-hairline/70 bg-surface shadow-card transition-shadow hover:shadow-cardhover">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
        aria-expanded={open}
      >
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2.5">
            <code className="truncate font-mono text-[0.88rem] font-medium text-ink">
              {review.path}
            </code>
            {review.language && (
              <span className="rounded-md bg-canvas px-1.5 py-0.5 text-[0.68rem] font-medium text-faint">
                {review.language}
              </span>
            )}
          </div>
          <p className="mt-1 truncate text-[0.83rem] text-subink">{review.summary}</p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <span className="hidden text-[0.78rem] text-faint sm:inline">
            {issueCount === 0 ? "No issues" : `${issueCount} issue${issueCount === 1 ? "" : "s"}`}
          </span>
          <VerdictPill verdict={review.verdict} />
          <svg
            className={`h-4 w-4 shrink-0 text-faint transition-transform duration-300 ${
              open ? "rotate-180" : ""
            }`}
            viewBox="0 0 20 20"
            fill="none"
          >
            <path
              d="M5 7.5 10 12.5 15 7.5"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </button>

      <div
        className={`grid overflow-hidden transition-[grid-template-rows] duration-300 ease-out ${
          open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        }`}
      >
        <div className="min-h-0">
          <div className="space-y-3 border-t border-hairline/70 px-5 pb-5 pt-4">
            <p className="text-[0.85rem] leading-relaxed text-subink">{review.justification}</p>
            {issueCount === 0 ? (
              <p className="rounded-xl bg-[#e6f6ea] px-4 py-3 text-[0.85rem] font-medium text-[#1e7a37]">
                Nothing to flag — clean pass.
              </p>
            ) : (
              <ul className="space-y-2.5">
                {review.issues.map((issue, i) => (
                  <li
                    key={i}
                    className="rounded-xl border border-hairline/70 bg-canvas/60 px-4 py-3"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <SeverityTag severity={issue.severity} category={issue.category} />
                      {issue.line != null && (
                        <span className="font-mono text-[0.72rem] text-faint">L{issue.line}</span>
                      )}
                    </div>
                    <p className="mt-1.5 text-[0.86rem] leading-relaxed text-ink">{issue.message}</p>
                    {issue.suggestion && (
                      <p className="mt-1.5 rounded-lg bg-accent-soft px-3 py-2 text-[0.82rem] italic leading-relaxed text-accent">
                        Suggestion: {issue.suggestion}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
