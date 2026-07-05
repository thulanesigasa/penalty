"use client";

import React, { useEffect, useState } from "react";
import { Activity, ShieldCheck, TrendingUp, Sparkles, CircleDot } from "lucide-react";
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
  const [isMounted, setIsMounted] = useState<boolean>(false);
  
  // Initialize the WebSocket connection using our custom hook
  const {
    isConnected,
    latestTelemetry,
    latestScreenshot,
    systemStats,
    history,
    sendCommand,
  } = useWebSocket(WS_URL);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-gray-200 p-6 md:p-10 flex flex-col gap-8">
      {/* Sticky Header Bar */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-[#0a0a0a]/80 border-b border-white/5 pb-5 pt-2 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary-electric to-accent-cyan flex items-center justify-center shadow-[0_0_15px_rgba(99,102,241,0.4)]">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent flex items-center gap-2">
              Penalty AI Shootout Bot
              <span className="text-[10px] px-2 py-0.5 bg-white/5 border border-white/10 rounded-md text-primary-electric font-semibold uppercase tracking-wide">
                Demo Mode
              </span>
            </h1>
            <p className="text-xs text-gray-400">
              Observing environment variables, executing shots, and compiling network rewards
            </p>
          </div>
        </div>
        
        {/* Connection status indicator */}
        <div className="flex items-center gap-2.5 px-4 py-2 rounded-xl bg-black/40 border border-white/5">
          <ShieldCheck className={`w-4 h-4 ${isConnected ? "text-success-emerald" : "text-danger-rose"}`} />
          <span className="text-xs font-semibold text-gray-300">
            {isConnected ? "WebSocket Online" : "Awaiting API Handshake"}
          </span>
        </div>
      </header>

      {/* Metrics Row Grid at the top */}
      <MetricsGrid systemStats={systemStats} />

      {/* Responsive Main Layout: 3 Columns on large screens */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        
        {/* Left Section (span 2): Render the PenaltyGrid & Win Rate Charts */}
        <div className="lg:col-span-2 flex flex-col gap-6 w-full">
          <PenaltyGrid
            gridState={latestTelemetry?.grid_state ?? null}
            targetShot={latestTelemetry?.target_shot ?? null}
            outcome={latestTelemetry?.outcome ?? null}
            qValues={latestTelemetry?.q_values ?? null}
          />

          {/* Training performance graphing metrics */}
          <div className="glass-panel rounded-2xl p-6 flex flex-col gap-5 border border-white/5 bg-black/40">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <div className="flex items-center gap-3">
                <TrendingUp className="text-primary-electric w-5 h-5" />
                <h2 className="text-lg font-semibold tracking-wide">Training Win Rate Trend</h2>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-primary-electric font-semibold uppercase">
                <Sparkles className="w-3.5 h-3.5" />
                Live Telemetry Feed
              </div>
            </div>

            <div className="h-[230px] w-full bg-black/20 rounded-xl p-2 border border-white/5">
              {isMounted && history.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis
                      dataKey="iteration"
                      stroke="rgba(255,255,255,0.3)"
                      fontSize={10}
                      tickLine={false}
                    />
                    <YAxis
                      stroke="rgba(255,255,255,0.3)"
                      fontSize={10}
                      tickLine={false}
                      domain={[0.0, 1.0]}
                      tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(13, 17, 33, 0.95)",
                        borderColor: "rgba(255, 255, 255, 0.1)",
                        borderRadius: "8px",
                      }}
                      labelStyle={{ color: "#888" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="win_rate"
                      name="Running Success"
                      stroke="hsl(195, 90%, 55%)"
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{ r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-xs text-gray-500 gap-2">
                  <CircleDot className="w-5 h-5 animate-pulse text-gray-600" />
                  <span>Awaiting telemetry updates to plot win rate trend line...</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Section (span 1): Render StateStream stacked above ControlPanel */}
        <div className="lg:col-span-1 flex flex-col gap-6 w-full">
          <StateStream latestScreenshot={latestScreenshot} />
          
          <ControlPanel
            isConnected={isConnected}
            sendCommand={sendCommand}
          />
        </div>

      </div>
    </div>
  );
}
