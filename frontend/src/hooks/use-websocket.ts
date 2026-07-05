import { useEffect, useRef, useState, useCallback } from "react";

export interface TelemetryPayload {
  iteration: number;
  target_shot: number;
  outcome: "WIN" | "LOSS" | "INVALID" | "ERROR";
  payout: number;
  profit_loss: number;
  epsilon: number;
  win_rate: number;
  loss: number;
  q_values: number[];
  grid_state: number[];
}

export interface SystemStats {
  totalIterations: number;
  winRate: number;
  totalProfit: number;
  currentEpsilon: number;
  loss: number;
}

export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [latestTelemetry, setLatestTelemetry] = useState<TelemetryPayload | null>(null);
  const [latestScreenshot, setLatestScreenshot] = useState<string | null>(null);
  const [systemStats, setSystemStats] = useState<SystemStats>({
    totalIterations: 0,
    winRate: 0.0,
    totalProfit: 0.0,
    currentEpsilon: 100.0,
    loss: 0.0,
  });
  const [history, setHistory] = useState<TelemetryPayload[]>([]);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    // Prevent duplicated connections if active
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) return;

    setIsConnected(false);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log("[WS Hook] WebSocket connection opened successfully.");
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        
        if (msg.type === "telemetry") {
          const payload = msg.payload as TelemetryPayload;
          setLatestTelemetry(payload);
          
          // Accumulate systemStats telemetry values
          setSystemStats((prev) => {
            // payout - stake (bet) is the profit for this step.
            // telemetry.profit_loss contains the exact reward value. We can accumulate profit.
            const reward = payload.profit_loss;
            return {
              totalIterations: payload.iteration,
              winRate: payload.win_rate,
              // If outcome is WIN, add reward. If LOSS, subtract stake. 
              // To match telemetry profit tracking, we accumulate reward values directly:
              totalProfit: prev.totalProfit + reward,
              currentEpsilon: payload.epsilon,
              loss: payload.loss,
            };
          });

          setHistory((prev) => {
            const nextHistory = [...prev, payload];
            if (nextHistory.length > 50) {
              nextHistory.shift();
            }
            return nextHistory;
          });
        } 
        
        else if (msg.type === "screenshot") {
          setLatestScreenshot(msg.payload.base64);
        }
      } catch (err) {
        console.error("[WS Hook] Error processing WebSocket message:", err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log("[WS Hook] WebSocket connection closed. Retrying in 3s...");
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = (err) => {
      console.error("[WS Hook] WebSocket error encountered:", err);
      ws.close();
    };
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [connect]);

  // Command Emitter
  const sendCommand = useCallback((action: "START" | "STOP" | "SET_SPEED" | "SET_BET", value?: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const command = {
        type: "command",
        action,
        ...(value !== undefined ? { value } : {}),
      };
      wsRef.current.send(JSON.stringify(command));
      console.log("[WS Hook] Emitted command command:", command);
    } else {
      console.warn("[WS Hook] WebSocket not open. Could not send command:", action);
    }
  }, []);

  return {
    isConnected,
    latestTelemetry,
    latestScreenshot,
    systemStats,
    history,
    sendCommand,
  };
}
