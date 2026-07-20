"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import NarrativeViewer from "@/components/NarrativeViewer";
import type { NarrativeResult } from "@/lib/api";

export default function ResultPage() {
  const router = useRouter();
  const [result, setResult] = useState<NarrativeResult | null>(null);

  useEffect(() => {
    const raw = sessionStorage.getItem("narrateResult");
    if (!raw) {
      router.replace("/");
      return;
    }
    setResult(JSON.parse(raw));
  }, [router]);

  if (!result) return null;

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50 flex flex-col items-center py-16 px-4">
      <div className="w-full max-w-3xl space-y-6">

        <div className="flex items-center justify-between">
          <button
            onClick={() => router.push("/")}
            className="text-sm text-gray-500 hover:text-gray-800 flex items-center gap-1"
          >
            ← New narrative
          </button>
          <span className="text-xs text-gray-400 bg-white border border-gray-200 px-3 py-1 rounded-full">
            Powered by IBM Granite
          </span>
        </div>

        <NarrativeViewer result={result} />

      </div>
    </main>
  );
}
