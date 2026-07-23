function formatTimestamp(iso: string) {
  return iso.slice(0, 19).replace("T", " ") + " UTC";
}

export function AlreadyAnalyzedBanner({
  sourceLabel,
  analyzedAt,
}: {
  sourceLabel: string;
  analyzedAt: string;
}) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-[#ff9500]/25 bg-[#fff2df] px-4 py-3.5 text-[#8a5300]">
      <svg className="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.6" />
        <path d="M10 6v4.5l3 2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
      <p className="text-[0.85rem] leading-relaxed">
        <span className="font-semibold">Already analyzed.</span>{" "}
        <code className="rounded bg-black/5 px-1 py-0.5 font-mono text-[0.8em]">{sourceLabel}</code>{" "}
        was reviewed on {formatTimestamp(analyzedAt)}. Showing the saved result — no re-run needed.
      </p>
    </div>
  );
}
