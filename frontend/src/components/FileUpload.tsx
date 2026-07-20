"use client";

import { useCallback, useState } from "react";
import { Upload } from "lucide-react";
import type { ParsedData } from "@/lib/api";
import { parseFile } from "@/lib/api";

interface Props {
  onParsed: (data: ParsedData, filename: string) => void;
}

export default function FileUpload({ onParsed }: Props) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handle = useCallback(
    async (file: File) => {
      setError(null);
      setLoading(true);
      try {
        const data = await parseFile(file);
        onParsed(data, file.name);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setLoading(false);
      }
    },
    [onParsed]
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handle(file);
  };

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handle(file);
  };

  return (
    <div className="w-full">
      <label
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`flex flex-col items-center justify-center gap-3 w-full h-48 rounded-xl border-2 border-dashed cursor-pointer transition-colors
          ${dragging ? "border-indigo-500 bg-indigo-50" : "border-gray-300 bg-gray-50 hover:bg-gray-100"}`}
      >
        <input
          type="file"
          accept=".csv,.pdf,.txt"
          className="hidden"
          onChange={onInputChange}
          disabled={loading}
        />
        {loading ? (
          <div className="flex flex-col items-center gap-2 text-gray-500">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm">Parsing file…</span>
          </div>
        ) : (
          <>
            <Upload className="w-8 h-8 text-gray-400" />
            <div className="text-center">
              <p className="text-sm font-medium text-gray-700">Drop a file or click to browse</p>
              <p className="text-xs text-gray-400 mt-1">CSV, PDF, or plain text</p>
            </div>
          </>
        )}
      </label>

      {error && (
        <p className="mt-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {error}
        </p>
      )}

      {/* Paste plain text fallback */}
      <details className="mt-3">
        <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
          Or paste raw text instead
        </summary>
        <PasteBox onParsed={onParsed} />
      </details>
    </div>
  );
}

function PasteBox({ onParsed }: Props) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!text.trim()) return;
    setLoading(true);
    const blob = new Blob([text], { type: "text/plain" });
    // File constructor types vary by lib — cast through unknown to avoid TS7009
    const file = new (window.File as unknown as new (
      parts: BlobPart[],
      name: string
    ) => File)([blob], "pasted-data.txt");
    try {
      const data = await parseFile(file);
      onParsed(data, "pasted-data.txt");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-2 flex flex-col gap-2">
      <textarea
        className="w-full h-32 text-sm border border-gray-200 rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
        placeholder="Paste CSV rows, report text, or any raw data…"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <button
        onClick={submit}
        disabled={loading || !text.trim()}
        className="self-end px-4 py-1.5 text-sm font-medium bg-indigo-600 text-white rounded-lg disabled:opacity-50 hover:bg-indigo-700"
      >
        {loading ? "Parsing…" : "Use this text"}
      </button>
    </div>
  );
}
