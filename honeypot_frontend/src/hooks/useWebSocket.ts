import { useEffect, useRef, useState, useCallback } from 'react';
import { getAccessToken } from '../api/client';
import type { WSAttackMessage } from '../types';

interface UseWebSocketOptions {
  onMessage?: (message: WSAttackMessage) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const { onMessage, reconnectAttempts = 5, reconnectInterval = 3000 } = options;
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isComponentMounted = useRef(true);
  const connectRef = useRef<() => void>(() => {});

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    const token = getAccessToken();
    if (!token) {
      setError(new Error('No access token available for WebSocket connection'));
      return;
    }

    // Determine WS URL based on current protocol and host
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // For local dev with vite proxy, we can connect to the proxy port
    const wsHost = import.meta.env.DEV ? window.location.host : (import.meta.env.VITE_API_URL?.replace(/^https?:\/\//, '') || window.location.host);
    const wsUrl = `${wsProtocol}//${wsHost}/api/v1/ws/attacks?token=${token}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (!isComponentMounted.current) {
          ws.close();
          return;
        }
        setIsConnected(true);
        setError(null);
        reconnectCountRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'attack' && onMessage) {
            onMessage(data as WSAttackMessage);
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message', e);
        }
      };

      ws.onclose = (event) => {
        if (!isComponentMounted.current) return;
        setIsConnected(false);
        
        // 1008 means policy violation (e.g. invalid token)
        if (event.code === 1008) {
          setError(new Error('WebSocket connection rejected (invalid token)'));
          return; // Don't reconnect on auth error
        }

        if (reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current += 1;
          // Exponential backoff
          const delay = reconnectInterval * Math.pow(1.5, reconnectCountRef.current - 1);
          reconnectTimeoutRef.current = setTimeout(() => {
            connectRef.current();
          }, Math.min(delay, 30000));
        } else {
          setError(new Error('WebSocket connection lost. Max reconnect attempts reached.'));
        }
      };

      ws.onerror = () => {
        if (!isComponentMounted.current) return;
        // The onclose handler will take care of reconnect logic
        setError(new Error('WebSocket connection error'));
      };

      wsRef.current = ws;
    } catch (e) {
      if (e instanceof Error) setError(e);
    }
  }, [onMessage, reconnectAttempts, reconnectInterval]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    isComponentMounted.current = true;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    connect();

    return () => {
      isComponentMounted.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const subscribe = useCallback((filters: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'subscribe', filters }));
    }
  }, []);

  return { isConnected, error, subscribe };
};
