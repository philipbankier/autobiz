import { ChatInterface } from "@/components/chat/chat-interface";

export default function ChatPage() {
  return (
    <div>
      <div className="mb-4">
        <h2 className="text-lg font-semibold">Chat with Agents</h2>
        <p className="text-sm text-muted-foreground">
          Send instructions and receive updates from your AI departments
        </p>
      </div>
      <ChatInterface />
    </div>
  );
}
