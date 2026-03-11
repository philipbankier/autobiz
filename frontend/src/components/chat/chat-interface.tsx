"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { DepartmentType, MessageRole } from "@/types";
import type { AgentMessage } from "@/types";
import { Send } from "lucide-react";

const departmentOptions = Object.values(DepartmentType).map((d) => ({
  value: d,
  label: d.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase()),
}));

const initialMessages: AgentMessage[] = [
  {
    id: "1",
    company_id: "1",
    department_type: DepartmentType.MARKETING,
    role: MessageRole.ASSISTANT,
    content:
      "Good morning! I've completed the content calendar for this week. We have 5 blog posts scheduled and 15 social media posts queued. Would you like me to adjust the posting schedule?",
    created_at: "2026-03-11T08:00:00Z",
  },
  {
    id: "2",
    company_id: "1",
    department_type: null,
    role: MessageRole.USER,
    content: "Looks great. Can you also draft a newsletter for our product launch next week?",
    created_at: "2026-03-11T08:05:00Z",
  },
  {
    id: "3",
    company_id: "1",
    department_type: DepartmentType.MARKETING,
    role: MessageRole.ASSISTANT,
    content:
      "Absolutely! I'll draft a newsletter highlighting the key features, early access benefits, and include a compelling CTA. I'll have a draft ready within the hour for your review.",
    created_at: "2026-03-11T08:05:30Z",
  },
  {
    id: "4",
    company_id: "1",
    department_type: DepartmentType.SALES,
    role: MessageRole.ASSISTANT,
    content:
      "Just a heads up -- I've identified 23 warm leads from last week's campaign. I'm preparing personalized outreach sequences for each. 8 leads have already opened our previous emails.",
    created_at: "2026-03-11T09:00:00Z",
  },
];

export function ChatInterface() {
  const [messages, setMessages] = useState<AgentMessage[]>(initialMessages);
  const [input, setInput] = useState("");
  const [department, setDepartment] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: AgentMessage = {
      id: String(Date.now()),
      company_id: "1",
      department_type: department ? (department as DepartmentType) : null,
      role: MessageRole.USER,
      content: input,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // Simulate agent response
    setTimeout(() => {
      const response: AgentMessage = {
        id: String(Date.now() + 1),
        company_id: "1",
        department_type: department ? (department as DepartmentType) : DepartmentType.MARKETING,
        role: MessageRole.ASSISTANT,
        content:
          "I've received your message and I'm working on it. I'll update you with results shortly.",
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, response]);
    }, 1000);
  }

  return (
    <div className="flex flex-col h-[calc(100vh-16rem)]">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === MessageRole.USER ? "flex-row-reverse" : ""}`}
          >
            <Avatar
              fallback={msg.role === MessageRole.USER ? "U" : "AI"}
              className={`h-8 w-8 shrink-0 ${
                msg.role === MessageRole.ASSISTANT ? "bg-primary/20" : "bg-secondary"
              }`}
            />
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2.5 ${
                msg.role === MessageRole.USER
                  ? "bg-primary text-primary-foreground"
                  : "bg-card border"
              }`}
            >
              {msg.department_type && msg.role === MessageRole.ASSISTANT && (
                <Badge variant="outline" className="mb-1 text-xs capitalize">
                  {msg.department_type.replace("_", " ")}
                </Badge>
              )}
              <p className="text-sm">{msg.content}</p>
              <span className="text-xs opacity-50 mt-1 block">
                {new Date(msg.created_at).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t p-4">
        <form onSubmit={handleSend} className="flex gap-2">
          <Select
            options={[{ value: "", label: "All Departments" }, ...departmentOptions]}
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            className="w-44 shrink-0"
          />
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Send a message to your agents..."
            className="flex-1"
          />
          <Button type="submit" size="icon" disabled={!input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
