"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import FileUpload from "@/components/FileUpload";
import ConfigPanel from "@/components/ConfigPanel";
import { generateNarrative, type ParsedData } from "@/lib/api";
import type { AudienceValue, ToneValue } from "@/lib/config";

const STEPS = ["Upload", "Configure", "Generate"] as const;
type Step = 0 | 1 | 2;

// Labels cycling through the 3 pipeline stages during generation
const PIPELINE_STAGES = [
  "Summarising your data…",
  "Extracting key insights…",
  "Writing your narrative…",
] as const;

export default function HomePage() {
  const router = useRouter();
  const [step, setStep]             = useState<Step>(0);
  const [parsedData, setParsed]     = useState<ParsedData | null>(null);
  const [filename, setFilename]     = useState("");
  const [audience, setAudience]     = useState<AudienceValue>("general_public");
  const [tone, setTone]             = useState<ToneValue>("storytelling");
  const [generating, setGenerating] = useState(false);
  const [error, setError]           = useState<string | null>(null);
  const [stageIdx, setStageIdx]     = useState(0);

  // Cycle through pipeline stage labels while generating
  useEffect(() => {
    if (!generating) { setStageIdx(0); return; }
    const id = setInterval(() => {
      setStageIdx((i) => Math.min(i + 1, PIPELINE_STAGES.length - 1));
    }, 8000); // advance ~every 8s (roughly per Watsonx step)
    return () => clearInterval(id);
  }, [generating]);

  const onParsed = (data: ParsedData, name: string) => {
    setParsed(data); setFilename(name); setError(null); setStep(1);
  };

  const goBack = () => { setError(null); setStep(0); };

  const onGenerate = useCallback(async () => {
    if (!parsedData || generating) return;
    setError(null); setGenerating(true); setStep(2);
    try {
      const result = await generateNarrative(parsedData, audience, tone);
      sessionStorage.setItem("narrateResult", JSON.stringify(result));
      router.push("/result");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
      setGenerating(false); setStep(1);
    }
  }, [parsedData, generating, audience, tone, router]);

  // Enter key triggers Generate on step 1
  useEffect(() => {
    if (step !== 1) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey && !generating) onGenerate();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [step, generating, onGenerate]);

  return (
    <main className="bg-grid min-h-screen flex flex-col items-center justify-start py-16 px-4">
      <div className="w-full max-w-xl space-y-8">

        {/* ── Wordmark ── */}
        <header className="text-center space-y-3 pb-2">
          <div className="inline-flex items-center gap-2 mb-1">
            <span className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 11 L7 3 L12 11" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M4.5 8h5" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
              </svg>
            </span>
            <h1 className="text-xl font-bold tracking-tight text-gray-900">Narrate-AI</h1>
          </div>
          <p className="text-gray-400 text-sm leading-relaxed max-w-xs mx-auto">
            Turn raw data into a compelling story — powered by IBM Granite.
          </p>
        </header>

        {/* ── Step indicator ── */}
        <div className="flex items-center justify-center gap-1">
          {STEPS.map((label, i) => {
            const isComplete = i < step;
            const isActive   = i === step;
            const canClick   = isComplete && !generating;
            return (
              <div key={label} className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => canClick && setStep(i as Step)}
                  disabled={!canClick}
                  title={canClick ? `Go back to ${label}` : undefined}
                  className={[
                    "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all",
                    isActive   ? "bg-indigo-600 text-white shadow-sm shadow-indigo-200"
                    : isComplete ? (canClick
                        ? "bg-indigo-100 text-indigo-700 hover:bg-indigo-200 cursor-pointer"
                        : "bg-indigo-100 text-indigo-600")
                    : "bg-gray-100 text-gray-400 cursor-default",
                  ].join(" ")}
                >
                  <span className={[
                    "w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold",
                    isActive    ? "bg-white/25 text-white"
                    : isComplete ? "bg-indigo-600 text-white"
                    : "bg-gray-200 text-gray-500",
                  ].join(" ")}>
                    {isComplete ? "✓" : i + 1}
                  </span>
                  {label}
                </button>
                {i < STEPS.length - 1 && (
                  <div className={`w-6 h-px mx-0.5 ${i < step ? "bg-indigo-300" : "bg-gray-200"}`} />
                )}
              </div>
            );
          })}
        </div>

        {/* ── Step 0 — Upload ── */}
        {step === 0 && (
          <section className="card p-7 space-y-4">
            <div>
              <h2 className="text-base font-semibold text-gray-800">Upload your data</h2>
              <p className="text-xs text-gray-400 mt-0.5">CSV, PDF, or plain text — we'll parse it automatically.</p>
            </div>
            <FileUpload onParsed={onParsed} />
          </section>
        )}

        {/* ── Step 1 — Configure ── */}
        {step === 1 && (
          <section className="card p-7 space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-gray-800">Configure output</h2>
                <p className="text-xs text-gray-400 mt-0.5">Choose how the story should be told.</p>
              </div>
              <span className="text-xs text-gray-400 bg-gray-100 border border-gray-200 px-2.5 py-1 rounded-full truncate max-w-[140px] font-mono">
                {filename}
              </span>
            </div>

            <ConfigPanel
              audience={audience} tone={tone}
              onAudienceChange={setAudience}
              onToneChange={setTone}
            />

            {error && (
              <div className="flex items-start gap-2.5 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
                <span className="shrink-0 mt-0.5">⚠</span>
                <span>{error}</span>
              </div>
            )}

            <div className="flex gap-2.5 pt-1">
              <button type="button" onClick={goBack} className="btn-ghost">
                ← Back
              </button>
              <button
                type="button" onClick={onGenerate} disabled={generating}
                className="btn-primary flex-1"
              >
                {generating ? "Generating…" : "Generate Narrative →"}
              </button>
            </div>
            <p className="text-center text-[11px] text-gray-300">Press Enter to generate</p>
          </section>
        )}

        {/* ── Step 2 — Generating ── */}
        {step === 2 && (
          <section className="card p-12 flex flex-col items-center gap-5">
            <div className="relative w-14 h-14">
              <div className="absolute inset-0 rounded-full bg-indigo-100 animate-ping opacity-50" />
              <div className="relative w-14 h-14 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
            <div className="text-center space-y-2">
              <p className="text-base font-semibold text-gray-800">Building your narrative…</p>
              {/* Stage label fades between pipeline steps */}
              <p key={stageIdx} className="text-sm text-indigo-500 font-medium animate-pulse">
                {PIPELINE_STAGES[stageIdx]}
              </p>
              <div className="flex items-center justify-center gap-1.5 pt-1">
                {PIPELINE_STAGES.map((_, i) => (
                  <div
                    key={i}
                    className={`h-1 rounded-full transition-all duration-700 ${
                      i <= stageIdx ? "w-6 bg-indigo-400" : "w-2 bg-gray-200"
                    }`}
                  />
                ))}
              </div>
            </div>
          </section>
        )}

      </div>
    </main>
  );
}
