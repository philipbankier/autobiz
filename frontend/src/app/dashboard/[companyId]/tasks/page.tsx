"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getTasks, createTask, type AgentTask } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const columns = ["todo", "in_progress", "done", "blocked"] as const;
const columnLabels: Record<string, string> = {
  todo: "📋 To Do", in_progress: "🔄 In Progress", done: "✅ Done", blocked: "🚫 Blocked",
};
const priorityColors: Record<string, string> = {
  low: "bg-gray-600", medium: "bg-blue-600", high: "bg-orange-600", urgent: "bg-red-600",
};
const departments = ["ceo", "developer", "marketing", "sales", "finance", "support"];

export default function TasksPage() {
  const params = useParams();
  const companyId = params.companyId as string;
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [assignedDept, setAssignedDept] = useState("developer");

  useEffect(() => {
    getTasks(companyId).then((res) => {
      if (res.data) setTasks(res.data);
      setLoading(false);
    });
  }, [companyId]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const res = await createTask(companyId, {
      title,
      description,
      priority,
      assigned_department: assignedDept,
    });
    if (res.data) {
      setTasks((prev) => [...prev, res.data!]);
      setTitle("");
      setDescription("");
      setShowForm(false);
    }
  }

  if (loading) return <p className="text-gray-400">Loading tasks...</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Task Board</h2>
        <Button onClick={() => setShowForm(!showForm)} size="sm">
          {showForm ? "Cancel" : "+ Add Task"}
        </Button>
      </div>

      {showForm && (
        <Card className="p-4 bg-gray-900 border-gray-800 mb-4">
          <form onSubmit={handleCreate} className="space-y-3">
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Task title" required className="bg-gray-800 border-gray-700 text-white" />
            <Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" rows={2} className="bg-gray-800 border-gray-700 text-white" />
            <div className="flex gap-3">
              <select value={priority} onChange={(e) => setPriority(e.target.value)} className="bg-gray-800 border border-gray-700 text-white rounded px-3 py-2 text-sm">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
              <select value={assignedDept} onChange={(e) => setAssignedDept(e.target.value)} className="bg-gray-800 border border-gray-700 text-white rounded px-3 py-2 text-sm">
                {departments.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
              <Button type="submit" size="sm">Create</Button>
            </div>
          </form>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {columns.map((col) => {
          const colTasks = tasks.filter((t) => t.status === col);
          return (
            <div key={col}>
              <h3 className="text-sm font-medium text-gray-400 mb-2">
                {columnLabels[col]} ({colTasks.length})
              </h3>
              <div className="space-y-2">
                {colTasks.map((task) => (
                  <Card key={task.id} className="p-3 bg-gray-900 border-gray-800">
                    <p className="text-white text-sm font-medium mb-1">{task.title}</p>
                    {task.description && (
                      <p className="text-gray-400 text-xs mb-2">{task.description}</p>
                    )}
                    <div className="flex items-center gap-2">
                      <Badge className={`text-xs ${priorityColors[task.priority] || "bg-gray-600"}`}>
                        {task.priority}
                      </Badge>
                      <span className="text-gray-500 text-xs capitalize">{task.assigned_department}</span>
                    </div>
                  </Card>
                ))}
                {colTasks.length === 0 && (
                  <p className="text-gray-600 text-xs text-center py-4">Empty</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
