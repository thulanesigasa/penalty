"use client";

import React from "react";
import { Monitor, HelpCircle, KeyRound, Globe, RefreshCw } from "lucide-react";

interface StateStreamProps {
  screenshot: string | null;
}

export function StateStream({ screenshot }: StateStreamProps) {
  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-5 h-full">
      <div className="flex items-center justify-between border-b border-white/5 pb-4">
        <div className="flex items-center gap-3">
          <Monitor className="text-primary-electric w-5 h-5" />
          <h2 className="text-lg font-semibold tracking-wide">Live Handoff Stream</h2>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center bg-black/40 rounded-xl border border-white/5 overflow-hidden min-h-[300px] relative">
        {screenshot ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={screenshot}
            alt="Live Automation Session Stream"
            className="w-full h-full object-cover object-center max-h-[450px]"
          />
        ) : (
          /* Interactive Configuration Onboarding Guide */
          <div className="flex flex-col items-center justify-center p-8 max-w-sm text-center gap-5">
            <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center relative">
              <Globe className="w-8 h-8 text-primary-electric" />
              <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-warning-amber border-2 border-bg-dark flex items-center justify-center animate-ping"></div>
              <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-warning-amber border-2 border-bg-dark flex items-center justify-center">
                <RefreshCw className="w-2.5 h-2.5 text-black animate-spin" />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <h3 className="text-sm font-semibold text-white">Awaiting Remote Chrome Connection</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Connect the automation script to stream the live game board. Follow the guidelines below.
              </p>
            </div>

            <div className="w-full flex flex-col gap-2.5 border-t border-white/5 pt-4 text-left">
              <div className="flex gap-2 text-xs text-gray-400">
                <span className="text-primary-electric font-semibold">1.</span>
                <span>Launch Chrome on port 9222.</span>
              </div>
              <div className="flex gap-2 text-xs text-gray-400">
                <span className="text-primary-electric font-semibold">2.</span>
                <span>Complete the login process manually in Chrome.</span>
              </div>
              <div className="flex gap-2 text-xs text-gray-400">
                <span className="text-primary-electric font-semibold">3.</span>
                <span>Run <code>python main.py</code> under the automation folder.</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
