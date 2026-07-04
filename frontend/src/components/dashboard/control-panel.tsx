"use client";

import React, { useState } from "react";
import { Play, Pause, Activity, Sliders, Circle } from "lucide-react";
import { ConnectionStatus } from "@/hooks/use-websocket";

interface ControlPanelProps {
  status: ConnectionStatus;
  startAgent: () => void;
  stopAgent: () => void;
  setSpeed: (val: number) => void;
  setBet: (val: number) => void;
}

export function ControlPanel({
  status,
  startAgent,
  stopAgent,
  setSpeed,
  setBet,
}: ControlPanelProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [speedVal, setSpeedVal] = useState(1.0);
  const [betVal, setBetVal] = useState(1.0);

  const handleStartStop = () => {
    if (isRunning) {
      stopAgent();
    } else {
      startAgent();
    }
    setIsRunning(!isRunning);
  };

  const handleSpeedChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setSpeedVal(val);
    setSpeed(val);
  };

  const handleBetChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setBetVal(val);
    setBet(val);
  };

  const statusColorMap = {
    CONNECTED: "text-success-emerald bg-success-emerald/10 border-success-emerald/20",
    CONNECTING: "text-warning-amber bg-warning-amber/10 border-warning-amber/20 animate-pulse",
    DISCONNECTED: "text-danger-rose bg-danger-rose/10 border-danger-rose/20",
  };

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6">
      <div className="flex items-center justify-between border-b border-white/5 pb-4">
        <div className="flex items-center gap-3">
          <Sliders className="text-primary-electric w-5 h-5" />
          <h2 className="text-lg font-semibold tracking-wide">System Controls</h2>
        </div>
        
        {/* Status Pill */}
        <div
          className={`px-3 py-1 text-xs font-semibold rounded-full border flex items-center gap-1.5 ${
            statusColorMap[status]
          }`}
        >
          <Circle className="w-2.5 h-2.5 fill-current" />
          {status}
        </div>
      </div>

      <div className="flex flex-col gap-5">
        {/* Play/Pause Button */}
        <button
          onClick={handleStartStop}
          disabled={status !== "CONNECTED"}
          className={`w-full py-3.5 px-6 rounded-xl font-bold flex items-center justify-center gap-2 transition-all cursor-pointer select-none active:scale-98 ${
            isRunning
              ? "bg-danger-rose hover:bg-danger-rose/90 text-white shadow-[0_0_20px_rgba(244,63,94,0.3)]"
              : "bg-primary-electric hover:bg-primary-electric/90 text-white shadow-[0_0_20px_rgba(99,102,241,0.3)]"
          } disabled:opacity-40 disabled:cursor-not-allowed`}
        >
          {isRunning ? (
            <>
              <Pause className="w-5 h-5 fill-current" /> Pause Training
            </>
          ) : (
            <>
              <Play className="w-5 h-5 fill-current" /> Start RL Training
            </>
          )}
        </button>

        {/* Speed Adjustment */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-sm text-gray-400">
            <span>Action Interval Delay</span>
            <span className="font-semibold text-white">{speedVal.toFixed(1)}s</span>
          </div>
          <input
            type="range"
            min="0.1"
            max="3.0"
            step="0.1"
            value={speedVal}
            onChange={handleSpeedChange}
            disabled={status !== "CONNECTED"}
            className="w-full h-1.5 rounded-lg appearance-none cursor-pointer bg-white/10 accent-primary-electric"
          />
        </div>

        {/* Bet Amount Adjustment */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-sm text-gray-400">
            <span>Demo Stake / Bet</span>
            <span className="font-semibold text-white">{betVal.toFixed(1)} USD</span>
          </div>
          <input
            type="range"
            min="1.0"
            max="20.0"
            step="1.0"
            value={betVal}
            onChange={handleBetChange}
            disabled={status !== "CONNECTED"}
            className="w-full h-1.5 rounded-lg appearance-none cursor-pointer bg-white/10 accent-primary-electric"
          />
        </div>
      </div>
    </div>
  );
}
