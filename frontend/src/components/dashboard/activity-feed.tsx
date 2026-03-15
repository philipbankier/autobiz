"use client";

import { useEffect, useRef, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { connectActivityStream, getActivityEvents } from "@/lib/api";

const eventTypeConfig: Record<string, { icon: string; color: string }> = {
  completed: { icon: "✓", color: "text-green-400" },
  started: { icon: "▶", color: "text-blue-400" },
  failed: { icon: "✗", color: "text-red-400" },
  warning: { icon: "⚠", color: "text-yellow-400" },
  skipped: { icon: "⏭", color: "text-gray-400" },
  error: { icon: "●", color: "text-red-400" },
  raw: { icon: "●", color: "text-gray-400" },
};

interface ActivityEvent {
  type: string;
  department?: string;
  message?: string;
  data?: string;
  timestamp?: string;
  [key: string]: unknown;
}

interface ActivityFeedProps {
  companyId: string;
}

export function ActivityFeed({ companyId }: ActivityFeedProps) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Load initial events
  useEffect(() => {
    getActivityEvents(companyId, 50).then((res) => {
      if (res.data) {
        setEvents(res.data as ActivityEvent[]);
      }
    });
  }, [companyId]);

  // SSE connection
  useEffect(() => {
    setConnected(true);
    const es = connectActivityStream(companyId, (event) => {
      const evt = event as ActivityEvent;
      if (evt.type === "error") {
        setConnected(false);
        return;
      }
      setEvents((prev) => {
        const next = [{ ...evt, timestamp: evt.timestamp || new Date().toISOString() }, ...prev];
        return next.slice(0, 50);
      });
    });

    return () => {
      es.close();
      setConnected(false);
    };
  }, [companyId]);

  // Auto-scroll on new events
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [events.length]);

  function timeAgo(dateStr: string | undefined): string {
    if (!dateStr) return "";
    const diff = Date.now() - new Date(dateStr).getTime();
    const secs = Math.floor(diff / 1000);
    if (secs < 60) return `${secs}s ago`;
    const mins = Math.floor(secs / 60);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  }

  return (
    <Card className="bg-gray-900 border-gray-800 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <h3 className="text-sm font-medium text-white">Activity Feed</h3>
        <div className="flex items-center gap-2">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              connected ? "bg-green-500 animate-pulse" : "bg-gray-600"
            }`}
          />
          <span className="text-xs text-gray-500">{connected ? "Live" : "Disconnected"}</span>
        </div>
      </div>

      {/* Events list */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto max-h-[400px] divide-y divide-gray-800/50">
        {events.length === 0 ? (
          <p className="text-gray-600 text-sm p-4">No activity yet</p>
        ) : (
          events.map((evt, i) => {
            const config = eventTypeConfig[evt.type] || eventTypeConfig.raw;
            return (
              <div key={i} className="px-4 py-2.5 hover:bg-gray-800/30 transition-colors">
                <div className="flex items-start gap-2">
                  <span className={`text-sm mt-0.5 ${config.color}`}>{config.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      {evt.department && (
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0 capitalize">
                          {evt.department}
                        </Badge>
                      )}
                      <span className="text-gray-600 text-[10px]">{timeAgo(evt.timestamp)}</span>
                    </div>
                    <p className="text-gray-300 text-xs truncate">
                      {evt.message || evt.data || evt.type}
                    </p>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
}
