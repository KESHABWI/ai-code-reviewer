"use client";

import { useRef, useState } from "react";
import { Spinner } from "./Spinner";

export function AnalyzeCard({
  onSubmitLink,
  onSubmitFile,
  loading,
}: {
  onSubmitLink: (url: string) => void;
  onSubmitFile: (file: File) => void;
  loading: boolean;
}) {
  const [githubUrl, setGithubUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const hasLink = githubUrl.trim().length > 0;
  const hasFile = file !== null;
  const canSubmit = (hasLink || hasFile) && !(hasLink && hasFile) && !loading;

  function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setFile(files[0]);
    setGithubUrl("");
  }

  function submit() {
    if (!canSubmit) return;
    if (hasLink) onSubmitLink(githubUrl.trim());
    else if (file) onSubmitFile(file);
  }

  return (
    <div className="rounded-xl3 border border-hairline/70 bg-surface p-5 shadow-card sm:p-7">
      <div className="grid gap-4 sm:grid-cols-[1.2fr_auto_1fr] sm:items-stretch sm:gap-5">
        <div className="flex flex-col justify-center">
          <label className="mb-1.5 text-[0.78rem] font-medium text-subink">GitHub repo link</label>
          <input
            type="text"
            value={githubUrl}
            onChange={(e) => {
              setGithubUrl(e.target.value);
              if (e.target.value) setFile(null);
            }}
            placeholder="https://github.com/owner/repo"
            disabled={loading || hasFile}
            className="w-full rounded-xl border border-hairline bg-canvas px-4 py-3 text-[0.92rem] text-ink placeholder:text-faint transition-colors focus:border-accent focus:bg-white focus:outline-none disabled:opacity-50"
          />
        </div>

        <div className="hidden items-center justify-center text-[0.75rem] font-medium uppercase tracking-wide text-faint sm:flex">
          or
        </div>

        <div className="flex flex-col justify-center">
          <label className="mb-1.5 text-[0.78rem] font-medium text-subink">
            Upload a .zip or single file
          </label>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              handleFiles(e.dataTransfer.files);
            }}
            onClick={() => inputRef.current?.click()}
            className={`flex cursor-pointer items-center gap-2.5 rounded-xl border px-4 py-3 transition-colors ${
              dragOver
                ? "border-accent bg-accent-soft"
                : "border-dashed border-hairline bg-canvas hover:border-accent/50"
            } ${hasLink ? "pointer-events-none opacity-50" : ""}`}
          >
            <svg className="h-4.5 w-4.5 shrink-0 text-faint" width={18} height={18} viewBox="0 0 20 20" fill="none">
              <path
                d="M10 13V4m0 0L6.5 7.5M10 4l3.5 3.5M4 13.5v1a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2v-1"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span className="truncate text-[0.88rem] text-subink">
              {file ? file.name : "Drag & drop, or click to browse"}
            </span>
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
          </div>
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between gap-4">
        <p className="text-[0.78rem] text-faint">
          {hasLink && hasFile
            ? "Provide only one — a link or an upload."
            : "One input, either kind — the engine figures out the rest."}
        </p>
        <button
          onClick={submit}
          disabled={!canSubmit}
          className="flex shrink-0 items-center gap-2 rounded-full bg-accent px-6 py-2.5 text-[0.88rem] font-semibold text-white shadow-pop transition-all hover:bg-accent-hover disabled:cursor-not-allowed disabled:bg-hairline disabled:text-faint disabled:shadow-none"
        >
          {loading ? (
            <>
              <Spinner size={16} />
              Analyzing…
            </>
          ) : (
            <>Analyze</>
          )}
        </button>
      </div>
    </div>
  );
}
