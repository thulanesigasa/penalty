"use client";

import React from "react";
import { TrendingUp, RefreshCw, BarChart2, ShieldAlert } from "lucide-react";
import { SystemStats } from "@/hooks/use-websocket";

interface MetricsGridProps {
  systemStats: SystemStats;
}

export function MetricsGrid({ systemStats }: MetricsGridProps) {
  const iteration = systemStats.totalIterations;
  const winRate = (systemStats.winRate * 100).toFixed(1);
  const profit = systemStats.totalProfit;
  const epsilon = (systemStats.currentEpsilon * 100).toFixed(1);

  const isLossVal = profit < 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
      {/* Iterations Card */}
      <div className="glass-panel rounded-2xl p-5 flex items-center justify-between bg-black/40 border border-white/5">
        <div className="flex flex-col gap-1">
          <span className="text-xs text-gray-400 font-medium uppercase tracking-wider">
            Total Iterations
          </span>
          <span className="text-3xl font-bold text-white tracking-tight font-mono">
            {iteration.toLocaleString()}
          </span>
        </div>
        <div className="w-12 h-12 rounded-xl bg-primary-electric/10 flex items-center justify-center border border-primary-electric/25">
          <RefreshCw className="w-6 h-6 text-primary-electric animate-[spin_8s_linear_infinite]" />
        </div>
      </div>

      {/* Win Rate Card */}
      <div className="glass-panel rounded-2xl p-5 flex items-center justify-between bg-black/40 border border-white/5">
        <div className="flex flex-col gap-1">
          <span className="text-xs text-gray-400 font-medium uppercase tracking-wider">
            Average Win Rate
          </span>
          <span className="text-3xl font-bold text-white tracking-tight font-mono">
            {winRate}%
          </span>
        </div>
        <div className="w-12 h-12 rounded-xl bg-accent-cyan/10 flex items-center justify-center border border-accent-cyan/25">
          <BarChart2 className="w-6 h-6 text-accent-cyan" />
        </div>
      </div>

      {/* Profit/Loss Card */}
      <div className="glass-panel rounded-2xl p-5 flex items-center justify-between bg-black/40 border border-white/5">
        <div className="flex flex-col gap-1">
          <span className="text-xs text-gray-400 font-medium uppercase tracking-wider">
            Cumulative Return
          </span>
          <span
            className={`text-3xl font-bold tracking-tight font-mono ${
              isLossVal ? "text-danger-rose" : "text-success-emerald"
            }`}
          >
            {profit >= 0 ? "+" : ""}
            {profit.toFixed(2)} USD
          </span>
        </div>
        <div
          className={`w-12 h-12 rounded-xl flex items-center justify-center border ${
            isLossVal
              ? "bg-danger-rose/10 border-danger-rose/25"
              : "bg-success-emerald/10 border-success-emerald/25"
          }`}
        >
          <TrendingUp
            className={`w-6 h-6 ${
              isLossVal ? "text-danger-rose" : "text-success-emerald"
            }`}
          />
        </div>
      </div>

      {/* Epsilon Card */}
      <div className="glass-panel rounded-2xl p-5 flex items-center justify-between bg-black/40 border border-white/5">
        <div className="flex flex-col gap-1">
          <span className="text-xs text-gray-400 font-medium uppercase tracking-wider">
            Exploration Rate (ε)
          </span>
          <span className="text-3xl font-bold text-white tracking-tight font-mono">
            {epsilon}%
          </span>
        </div>
        <div className="w-12 h-12 rounded-xl bg-warning-amber/10 flex items-center justify-center border border-warning-amber/25">
          <ShieldAlert className="w-6 h-6 text-warning-amber" />
        </div>
      </div>
    </div>
  );
}
