import type { Severity, Verdict } from "@/lib/types";

const VERDICT_STYLE: Record<Verdict, { bg: string; fg: string; dot: string; label: string }> = {
  Approve: { bg: "bg-[#e6f6ea]", fg: "text-[#1e7a37]", dot: "bg-[#2fa64b]", label: "Approve" },
  "Request Changes": {
    bg: "bg-[#fde8e7]",
    fg: "text-[#c0271d]",
    dot: "bg-[#ff3b30]",
    label: "Request changes",
  },
  Comment: { bg: "bg-[#fff2df]", fg: "text-[#a85d00]", dot: "bg-[#ff9500]", label: "Comment" },
};

const SEVERITY_STYLE: Record<Severity, { bg: string; fg: string; ring: string }> = {
  Blocking: { bg: "bg-[#fde8e7]", fg: "text-[#c0271d]", ring: "border-[#ff3b30]/25" },
  Suggestion: { bg: "bg-[#fff2df]", fg: "text-[#a85d00]", ring: "border-[#ff9500]/25" },
  Nitpick: { bg: "bg-accent-soft", fg: "text-accent", ring: "border-accent/20" },
};

export function VerdictPill({ verdict }: { verdict: Verdict }) {
  const s = VERDICT_STYLE[verdict] ?? VERDICT_STYLE.Comment;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[0.8rem] font-semibold ${s.bg} ${s.fg}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  );
}

export function SeverityTag({ severity, category }: { severity: Severity; category: string }) {
  const s = SEVERITY_STYLE[severity] ?? SEVERITY_STYLE.Nitpick;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[0.68rem] font-semibold uppercase tracking-wide ${s.bg} ${s.fg} ${s.ring}`}
    >
      {severity} · {category}
    </span>
  );
}
