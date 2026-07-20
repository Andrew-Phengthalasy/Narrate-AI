"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import FileUpload from "@/components/FileUpload";
import ConfigPanel from "@/components/ConfigPanel";
import { generateNarrative, type ParsedData } from "@/lib/api";
import type { AudienceValue, ToneValue } from "@/lib/config";

const STEPS = ["Upload", "Configure", "Generate"] as const;

type Step = 0 | 1 | 2;

export default function HomePage() {
  const router = useRouter();
  const [step, setStep]         = useState<Step>(0);
  const [parsedData, setParsed] = useState<ParsedData | null>(null);
  const [filename, setFilename] = useState("");
  const [audience, setAudience] = useState<AudienceValue>("general_public");
  const [tone, setTone]         = useState<ToneValue>("storytelling");
  const [generating, setGenerating] = useState(false);
  const [error, setError]       = useState<string | null>(null);

  const onParsed = (data: ParsedData, name: string) => {
    setParsed(data);
    setFilename(name);
    setStep(1);
  };

  const onGenerate = async () => {
    if (!parsedData) return;
    setError(null);
    setGenerating(true);
    setStep(2);
    try {
      const result = await generateNarrative(parsedData, audience, tone);
      // Persist result to sessionStorage so the result page can read it
      sessionStorage.setItem("narrateResult", JSON.stringify(result));
      router.push("/result");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
      setGenerating(false);
      setStep(1);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50 flex flex-col items-center py-16 px-4">
      <div className="w-full max-w-2xl space-y-10">

        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">Narrate-AI</h1>
          <p className="text-gray-500 text-lg">Turn raw data into a compelling story — in seconds.</p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2">
          {STEPS.map((label, i) => (
            <div key={label} className="flex items-center gap-2">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold
                ${i < step ? "bg-indigo-600 text-white"
                  : i === step ? "bg-indigo-100 text-indigo-700 ring-2 ring-indigo-400"
                  : "bg-gray-100 text-gray-400"}`}>
                {i < step ? "✓" : i + 1}
              </div>
              <span className={`text-sm ${i === step ? "text-indigo-700 font-medium" : "text-gray-400"}`}>
                {label}
              </span>
              {i < STEPS.length - 1 && <div className="w-8 h-px bg-gray-200 mx-1" />}
            </div>
          ))}
        </div>

        {/* Step 0 — Upload */}
        {step === 0 && (
          <section className="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm space-y-4">
            <h2 className="text-lg font-semibold text-gray-800">Upload your data</h2>
            <FileUpload onParsed={onParsed} />
          </section>
        )}

        {/* Step 1 — Configure */}
        {step === 1 && (
          <section className="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-800">Configure output</h2>
              <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full">{filename}</span>
            </div>

            <ConfigPanel
              audience={audience}
              tone={tone}
              onAudienceChange={setAudience}
              onToneChange={setTone}
            />

            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setStep(0)}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                ← Back
              </button>
              <button
                onClick={onGenerate}
                className="flex-1 py-2.5 text-sm font-semibold bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Generate Narrative →
              </button>
            </div>
          </section>
        )}

        {/* Step 2 — Generating */}
        {step === 2 && generating && (
          <section className="bg-white rounded-2xl border border-gray-200 p-12 shadow-sm flex flex-col items-center gap-6">
            <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <div className="text-center space-y-1">
              <p className="text-lg font-semibold text-gray-800">Building your narrative…</p>
              <p className="text-sm text-gray-500">Summarising data → Extracting insights → Writing story</p>
            </div>
          </section>
        )}

      </div>
    </main>
  );
}
