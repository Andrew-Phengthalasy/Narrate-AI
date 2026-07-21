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
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">

      {/* ── Audience ── */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2.5">Audience</p>
        <div className="flex flex-col gap-1.5">
          {AUDIENCES.map((a) => {
            const active = audience === a.value;
            return (
              <button
                type="button"
                key={a.value}
                onClick={() => onAudienceChange(a.value)}
                className={[
                  "relative text-left px-4 py-3 rounded-xl border transition-all duration-100 overflow-hidden",
                  active
                    ? "border-indigo-300 bg-indigo-50"
                    : "border-gray-200 hover:border-gray-300 hover:bg-gray-50/80",
                ].join(" ")}
              >
                {/* Active left bar */}
                {active && (
                  <span className="absolute left-0 inset-y-0 w-[3px] bg-indigo-500 rounded-r-full" />
                )}
                <span className={`block text-sm font-medium ${active ? "text-indigo-800" : "text-gray-700"}`}>
                  {a.label}
                </span>
                <span className={`block text-xs mt-0.5 ${active ? "text-indigo-500" : "text-gray-400"}`}>
                  {a.description}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Tone ── */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2.5">Tone</p>
        <div className="flex flex-col gap-1.5">
          {TONES.map((t) => {
            const active = tone === t.value;
            return (
              <button
                type="button"
                key={t.value}
                onClick={() => onToneChange(t.value)}
                className={[
                  "relative text-left px-4 py-3 rounded-xl border transition-all duration-100 overflow-hidden",
                  active
                    ? "border-violet-300 bg-violet-50"
                    : "border-gray-200 hover:border-gray-300 hover:bg-gray-50/80",
                ].join(" ")}
              >
                {active && (
                  <span className="absolute left-0 inset-y-0 w-[3px] bg-violet-500 rounded-r-full" />
                )}
                <span className={`block text-sm font-medium ${active ? "text-violet-800" : "text-gray-700"}`}>
                  {t.label}
                </span>
                <span className={`block text-xs mt-0.5 ${active ? "text-violet-500" : "text-gray-400"}`}>
                  {t.description}
                </span>
              </button>
            );
          })}
        </div>
      </div>

    </div>
  );
}
