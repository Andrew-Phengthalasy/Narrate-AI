"use client";

import { AUDIENCES, TONES, type AudienceValue, type ToneValue } from "@/lib/config";

interface Props {
  audience: AudienceValue;
  tone: ToneValue;
  onAudienceChange: (v: AudienceValue) => void;
  onToneChange: (v: ToneValue) => void;
}

export default function ConfigPanel({ audience, tone, onAudienceChange, onToneChange }: Props) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
      {/* Audience */}
      <div>
        <p className="text-sm font-semibold text-gray-700 mb-3">Target Audience</p>
        <div className="flex flex-col gap-2">
          {AUDIENCES.map((a) => (
            <button
              key={a.value}
              onClick={() => onAudienceChange(a.value)}
              className={`text-left px-4 py-3 rounded-xl border transition-colors
                ${audience === a.value
                  ? "border-indigo-500 bg-indigo-50 text-indigo-800"
                  : "border-gray-200 hover:border-gray-300 text-gray-700"}`}
            >
              <span className="block text-sm font-medium">{a.label}</span>
              <span className="block text-xs text-gray-500 mt-0.5">{a.description}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tone */}
      <div>
        <p className="text-sm font-semibold text-gray-700 mb-3">Tone</p>
        <div className="flex flex-col gap-2">
          {TONES.map((t) => (
            <button
              key={t.value}
              onClick={() => onToneChange(t.value)}
              className={`text-left px-4 py-3 rounded-xl border transition-colors
                ${tone === t.value
                  ? "border-violet-500 bg-violet-50 text-violet-800"
                  : "border-gray-200 hover:border-gray-300 text-gray-700"}`}
            >
              <span className="block text-sm font-medium">{t.label}</span>
              <span className="block text-xs text-gray-500 mt-0.5">{t.description}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
