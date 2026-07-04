"use client";

import React from "react";
import { Target } from "lucide-react";

interface PenaltyGridProps {
  gridState: number[] | null;
  targetShot: number | null;
  outcome: string | null;
  qValues: number[] | null;
}

export function PenaltyGrid({
  gridState,
  targetShot,
  outcome,
  qValues,
}: PenaltyGridProps) {
  // Setup 12 default grids if null
  const activeGrid = gridState || Array(12).fill(0);
  const activeQ = qValues || Array(12).fill(0.0);

  // Normalize Q-values for the heatmap overlay (0 to 1 scale)
  const minQ = Math.min(...activeQ);
  const maxQ = Math.max(...activeQ);
  const qRange = maxQ - minQ || 1.0;

  const getHeatmapColor = (qVal: number) => {
    // High Q-value -> purple glow overlay
    const normalized = (qVal - minQ) / qRange;
    return `rgba(99, 102, 241, ${normalized * 0.25})`;
  };

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-5 flex-1">
      <div className="flex items-center gap-3 border-b border-white/5 pb-4">
        <Target className="text-primary-electric w-5 h-5" />
        <div>
          <h2 className="text-lg font-semibold tracking-wide">Penalty Shooting Grid</h2>
          <p className="text-xs text-gray-400">Heatmap shows AI Q-value selection strategy (purple = high priority)</p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 aspect-[4/3] w-full max-w-[600px] mx-auto bg-black/30 rounded-xl p-4 border border-white/5 relative">
        
        {/* Goal Post lines styling to look like football goal */}
        <div className="absolute top-0 left-4 right-4 h-2 border-t-2 border-x-2 border-white/20 rounded-t-lg"></div>

        {Array(12)
          .fill(null)
          .map((_, index) => {
            const isHit = activeGrid[index] === 1;
            const isShot = targetShot === index;
            const qVal = activeQ[index];
            const bgHeat = getHeatmapColor(qVal);
            
            // Determine border and active states
            let cellStyle = "border-white/5 bg-white/2 hover:bg-white/5";
            let glowLayer = null;

            if (isShot) {
              if (outcome === "WIN") {
                cellStyle = "border-success-emerald/50 bg-success-emerald/15 shadow-[0_0_20px_rgba(16,185,129,0.3)]";
                glowLayer = <span className="absolute inset-0 bg-success-emerald/20 animate-ping rounded-xl pointer-events-none"></span>;
              } else if (outcome === "LOSS") {
                cellStyle = "border-danger-rose/50 bg-danger-rose/15 shadow-[0_0_20px_rgba(244,63,94,0.3)]";
                glowLayer = <span className="absolute inset-0 bg-danger-rose/20 animate-ping rounded-xl pointer-events-none"></span>;
              } else {
                cellStyle = "border-primary-electric bg-primary-electric/15 glow-active";
              }
            } else if (isHit) {
              cellStyle = "border-white/10 bg-white/5 opacity-40";
            }

            return (
              <div
                key={index}
                style={{ backgroundColor: !isShot && !isHit ? bgHeat : undefined }}
                className={`relative flex flex-col items-center justify-center border-2 rounded-xl transition-all duration-300 p-2 select-none group cursor-pointer ${cellStyle}`}
              >
                {glowLayer}
                
                {/* Spot Index Number */}
                <span className="absolute top-1.5 left-2 text-[10px] text-gray-500 font-bold">
                  #{index}
                </span>

                {/* Main Node Graphic */}
                <div className="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center bg-black/40 group-hover:scale-110 transition-transform shadow-inner">
                  {isShot ? (
                    <span
                      className={`w-3.5 h-3.5 rounded-full ${
                        outcome === "WIN"
                          ? "bg-success-emerald shadow-[0_0_8px_hsl(150,84%,58%)]"
                          : outcome === "LOSS"
                          ? "bg-danger-rose shadow-[0_0_8px_hsl(342,85%,60%)]"
                          : "bg-primary-electric shadow-[0_0_8px_hsl(250,95%,65%)]"
                      }`}
                    ></span>
                  ) : (
                    <span className={`w-2.5 h-2.5 rounded-full bg-white/20 group-hover:bg-white/40 transition-colors ${isHit ? "bg-white/5" : ""}`}></span>
                  )}
                </div>

                {/* Q-Value display */}
                {!isHit && (
                  <span className="text-[10px] text-gray-400 mt-1 font-mono font-medium">
                    {qVal >= 0 ? "+" : ""}
                    {qVal.toFixed(2)}
                  </span>
                )}
                {isHit && (
                  <span className="text-[9px] text-gray-500 mt-1 uppercase tracking-tight font-semibold">
                    Cleared
                  </span>
                )}
              </div>
            );
          })}
      </div>
    </div>
  );
}
