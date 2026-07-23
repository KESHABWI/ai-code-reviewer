"use client";

import { useEffect, useState } from "react";
import { getHistory } from "@/lib/api";
import type { HistoryEntry } from "@/lib/types";
import { Spinner } from "../Spinner";

const SOURCE_LABEL: Record<string, string> = {
  github: "GitHub",
  zip: "Zip",
  file: "File",
};

export function HistoryPanel() {
  const [items, setItems] = useState<HistoryEntry[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setItems(await getHistory());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't load history.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-[0.8rem] text-faint">Every repo, zip, and file reviewed so far.</p>
        <button
          onClick={load}
          className="flex items-center gap-1.5 rounded-full border border-hairline px-3.5 py-1.5 text-[0.78rem] font-medium text-subink transition-colors hover:border-accent hover:text-accent"
        >
          {loading && <Spinner size={12} />}
          Refresh
        </button>
      </div>

      {error && <p className="text-[0.82rem] text-danger">{error}</p>}

      {items && items.length === 0 && (
        <p className="rounded-xl border border-dashed border-hairline bg-canvas px-4 py-6 text-center text-[0.85rem] text-faint">
          Nothing analyzed yet.
        </p>
      )}

      <ul className="divide-y divide-hairline/70 overflow-hidden rounded-2xl border border-hairline/70 bg-surface">
        {items?.map((item, i) => (
          <li key={i} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
            <div className="min-w-0">
              <p className="truncate text-[0.87rem] font-medium text-ink">{item.source_label}</p>
              <p className="mt-0.5 font-mono text-[0.72rem] text-faint">
                {item.identifier.slice(0, 12)}
              </p>
            </div>
            <div className="flex items-center gap-2 text-[0.75rem] text-faint">
              <span className="rounded-md bg-canvas px-2 py-0.5 font-medium text-subink">
                {SOURCE_LABEL[item.source_type] ?? item.source_type}
              </span>
              <span>{item.analyzed_at.slice(0, 19).replace("T", " ")} UTC</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
