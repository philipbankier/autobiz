"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import { getChat, sendChat, type AgentMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const departments = ["ceo", "developer", "marketing", "sales", "finance", "support"];
const deptIcons: Record<string, string> = {
  ceo: "👔", developer: "💻", marketing: "📢", sales: "💰", finance: "📊", support: "🎧",
};

export default function ChatPage() {
  const params = useParams();
  const companyId = params.companyId as string;
  const [selectedDept, setSelectedDept] = useState("ceo");
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getChat(companyId, selectedDept).then((res) => {
      if (res.data) setMessages(res.data);
    });
  }, [companyId, selectedDept]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    setSending(true);

    const res = await sendChat(companyId, selectedDept, input.trim());
    setSending(false);
    setInput("");

    if (res.data) {
      setMessages((prev) => [...prev, res.data!.user_message, res.data!.agent_message]);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-220px)]">
      {/* Department selector */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {departments.map((dept) => (
          <button
            key={dept}
            onClick={() => setSelectedDept(dept)}
            className={`px-3 py-1.5 rounded text-sm transition-colors ${
              selectedDept === dept
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-400 hover:text-white"
            }`}
          >
            {deptIcons[dept]} {dept}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 bg-gray-900 rounded-lg p-4 border border-gray-800">
        {messages.length === 0 && (
          <p className="text-gray-500 text-center py-8">
            No messages yet. Send a message to the {selectedDept} department.
          </p>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[70%] rounded-lg px-4 py-2 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-200"
              }`}
            >
              <p className="text-sm">{msg.content}</p>
              <p className="text-xs opacity-50 mt-1">
                {new Date(msg.created_at).toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="flex gap-2 mt-3">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Message the ${selectedDept} department...`}
          className="flex-1 bg-gray-800 border-gray-700 text-white"
          disabled={sending}
        />
        <Button type="submit" disabled={sending || !input.trim()}>
          {sending ? "..." : "Send"}
        </Button>
      </form>
    </div>
  );
}
