"use client";

import { useCallback, useState } from "react";
import { Upload } from "lucide-react";
import type { ParsedData } from "@/lib/api";
import { parseFile } from "@/lib/api";

interface Props {
  onParsed: (data: ParsedData, filename: string) => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileUpload({ onParsed }: Props) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<File | null>(null);

  const handle = useCallback(
    async (file: File) => {
      setError(null);
      setPending(file);
      setLoading(true);
      try {
        const data = await parseFile(file);
        onParsed(data, file.name);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
        setPending(null);
      } finally {
        setLoading(false);
      }
    },
    [onParsed]
  );

  // Track drag depth to avoid flickering when cursor moves over child elements
  const [dragDepth, setDragDepth] = useState(0);

  const onDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setDragDepth((d) => d + 1);
    setDragging(true);
  };

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragDepth((d) => {
      const next = d - 1;
      if (next <= 0) setDragging(false);
      return next;
    });
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    setDragDepth(0);
    const file = e.dataTransfer.files[0];
    if (file) handle(file);
  };

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handle(file);
    // Reset input value so the same file can be re-selected
    e.target.value = "";
  };

  return (
    <div className="w-full">
      <label
        onDragEnter={onDragEnter}
        onDragOver={(e) => e.preventDefault()}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={[
          "flex flex-col items-center justify-center gap-3 w-full h-44 rounded-xl border-2 border-dashed cursor-pointer transition-all duration-150",
          dragging
            ? "border-indigo-400 bg-indigo-50 scale-[1.01]"
            : "border-gray-200 bg-gray-50/60 hover:bg-gray-50 hover:border-gray-300",
        ].join(" ")}
      >
        <input
          type="file"
          accept=".csv,.pdf,.txt"
          className="hidden"
          onChange={onInputChange}
          disabled={loading}
        />
        {loading && pending ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-gray-600 font-medium">{pending.name}</span>
            <span className="text-xs text-gray-400">{formatBytes(pending.size)}</span>
          </div>
        ) : (
          <>
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center">
              <Upload className="w-5 h-5 text-indigo-500" />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-gray-700">Drop a file or <span className="text-indigo-600">click to browse</span></p>
              <p className="text-xs text-gray-400 mt-0.5">CSV, PDF, or plain text · max 10 MB</p>
            </div>
          </>
        )}
      </label>

      {error && (
        <div className="mt-2 flex items-start gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2.5">
          <span className="shrink-0 mt-0.5">⚠</span>
          <span>{error}</span>
        </div>
      )}

      {/* Paste plain text fallback */}
      <details className="mt-3">
        <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600 select-none transition-colors">
          Or paste raw text instead ↓
        </summary>
        <PasteBox onParsed={onParsed} />
      </details>
    </div>
  );
}

function PasteBox({ onParsed }: Props) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (!text.trim()) return;
    setError(null);
    setLoading(true);
    const file = new File([new Blob([text], { type: "text/plain" })], "pasted-data.txt");
    try {
      const data = await parseFile(file);
      onParsed(data, "pasted-data.txt");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to parse pasted text");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-3 flex flex-col gap-2">
      <textarea
        className="w-full h-32 text-sm border border-gray-200 rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-gray-50 placeholder:text-gray-400"
        placeholder="Paste CSV rows, report text, or any raw data…"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      {error && (
        <div className="flex items-start gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          <span className="shrink-0">⚠</span><span>{error}</span>
        </div>
      )}
      <button
        type="button"
        onClick={submit}
        disabled={loading || !text.trim()}
        className="btn-primary self-end h-9 px-4 text-xs"
      >
        {loading ? "Parsing…" : "Use this text"}
      </button>
    </div>
  );
}
