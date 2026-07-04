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

export type ConnectionStatus = "CONNECTING" | "CONNECTED" | "DISCONNECTED";

export function useWebSocket(url: string) {
  const [status, setStatus] = useState<ConnectionStatus>("DISCONNECTED");
  const [telemetry, setTelemetry] = useState<TelemetryPayload | null>(null);
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [history, setHistory] = useState<TelemetryPayload[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) return;

    setStatus("CONNECTING");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("CONNECTED");
      console.log("WebSocket connected to dashboard endpoint");
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "telemetry") {
          const payload = msg.payload as TelemetryPayload;
          setTelemetry(payload);
          setHistory((prev) => {
            // Cap history length at 50 elements for active dashboard performance
            const nextHistory = [...prev, payload];
            if (nextHistory.length > 50) {
              nextHistory.shift();
            }
            return nextHistory;
          });
        } else if (msg.type === "screenshot") {
          setScreenshot(msg.payload.base64);
        }
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    ws.onclose = () => {
      setStatus("DISCONNECTED");
      console.log("WebSocket disconnected. Reconnecting in 3s...");
      setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendCommand = useCallback((action: string, value?: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "command",
          action,
          ...(value !== undefined ? { value } : {}),
        })
      );
    }
  }, []);

  const startAgent = useCallback(() => sendCommand("START"), [sendCommand]);
  const stopAgent = useCallback(() => sendCommand("STOP"), [sendCommand]);
  const setSpeed = useCallback((val: number) => sendCommand("SET_SPEED", val), [sendCommand]);
  const setBet = useCallback((val: number) => sendCommand("SET_BET", val), [sendCommand]);

  return {
    status,
    telemetry,
    screenshot,
    history,
    startAgent,
    stopAgent,
    setSpeed,
    setBet,
  };
}
