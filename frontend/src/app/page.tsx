"use client";

import React, { useEffect, useState } from "react";
import { Activity, CircleDot, ShieldCheck, TrendingUp, Sparkles } from "lucide-react";
import { useWebSocket } from "@/hooks/use-websocket";
import { MetricsGrid } from "@/components/dashboard/metrics-grid";
import { ControlPanel } from "@/components/dashboard/control-panel";
import { PenaltyGrid } from "@/components/dashboard/penalty-grid";
import { StateStream } from "@/components/dashboard/state-stream";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/dashboard";

export default function DashboardPage() {
  const [isMounted, setIsMounted] = useState(false);
  const {
    status,
    telemetry,
    screenshot,
    history,
    startAgent,
    stopAgent,
    setSpeed,
    setBet,
  } = useWebSocket(WS_URL);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  return (
    <main className="min-h-screen p-6 md:p-10 flex flex-col gap-8">
      {/* Header Bar */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-white/5 pb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary-electric to-accent-cyan flex items-center justify-center shadow-[0_0_15px_rgba(99,102,241,0.4)]">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent flex items-center gap-2">
              Penalty RL Bot Dashboard <span className="text-xs px-2 py-0.5 bg-white/5 border border-white/10 rounded-md text-primary-electric font-semibold uppercase tracking-wide">Demo Account</span>
            </h1>
            <p className="text-xs md:text-sm text-gray-400">
              Observing game states, training models, and executing actions in real time
            </p>
          </div>
        </div>
        
        {/* API Connection Indicator */}
        <div className="flex items-center gap-2.5 px-4 py-2 rounded-xl bg-white/5 border border-white/5">
          <ShieldCheck className="w-4 h-4 text-success-emerald" />
          <span className="text-xs font-semibold text-gray-300">FastAPI Bridge API Active</span>
        </div>
      </header>

      {/* Metrics Row */}
      <MetricsGrid telemetry={telemetry} />

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Controls Column */}
        <div className="flex flex-col gap-6 lg:col-span-1">
          <ControlPanel
            status={status}
            startAgent={startAgent}
            stopAgent={stopAgent}
            setSpeed={setSpeed}
            setBet={setBet}
          />
          <StateStream screenshot={screenshot} />
        </div>

        {/* Penalty Visualizer and Live Chart Column */}
        <div className="flex flex-col gap-6 lg:col-span-2">
          
          {/* Penalty Shooting Grid */}
          <PenaltyGrid
            gridState={telemetry?.grid_state ?? null}
            targetShot={telemetry?.target_shot ?? null}
            outcome={telemetry?.outcome ?? null}
            qValues={telemetry?.q_values ?? null}
          />

          {/* Performance Chart Card */}
          <div className="glass-panel rounded-2xl p-6 flex flex-col gap-5">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <div className="flex items-center gap-3">
                <TrendingUp className="text-primary-electric w-5 h-5" />
                <h2 className="text-lg font-semibold tracking-wide">Training Win Rate Trend</h2>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-primary-electric font-semibold uppercase">
                <Sparkles className="w-3.5 h-3.5" />
                DQN Network Telemetry
              </div>
            </div>

            <div className="h-[250px] w-full bg-black/20 rounded-xl p-2 border border-white/5">
              {isMounted && history.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis
                      dataKey="iteration"
                      stroke="rgba(255,255,255,0.3)"
                      fontSize={11}
                      tickLine={false}
                    />
                    <YAxis
                      stroke="rgba(255,255,255,0.3)"
                      fontSize={11}
                      tickLine={false}
                      domain={[0.0, 1.0]}
                      tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(13, 17, 33, 0.9)",
                        borderColor: "rgba(255, 255, 255, 0.1)",
                        borderRadius: "8px",
                      }}
                      labelStyle={{ color: "#888" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="win_rate"
                      name="Running Win Rate"
                      stroke="hsl(195, 90%, 55%)"
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-xs text-gray-500 gap-2">
                  <CircleDot className="w-5 h-5 animate-pulse text-gray-600" />
                  <span>Awaiting training steps to plot live win rate trend...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
