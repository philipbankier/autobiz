"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Dialog, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { TaskStatus, TaskPriority, DepartmentType } from "@/types";
import type { AgentTask } from "@/types";
import { Plus, GripVertical } from "lucide-react";

const columns = [
  { status: TaskStatus.TODO, label: "To Do", color: "text-muted-foreground" },
  { status: TaskStatus.IN_PROGRESS, label: "In Progress", color: "text-blue-500" },
  { status: TaskStatus.DONE, label: "Done", color: "text-emerald-500" },
  { status: TaskStatus.BLOCKED, label: "Blocked", color: "text-red-500" },
];

const priorityVariant = {
  [TaskPriority.CRITICAL]: "destructive" as const,
  [TaskPriority.HIGH]: "warning" as const,
  [TaskPriority.MEDIUM]: "secondary" as const,
  [TaskPriority.LOW]: "outline" as const,
};

const mockTasks: AgentTask[] = [
  {
    id: "1",
    company_id: "1",
    department_type: DepartmentType.MARKETING,
    title: "Create Q1 content calendar",
    description: "Plan and schedule all content for Q1 across blog, social, and email.",
    status: TaskStatus.DONE,
    priority: TaskPriority.HIGH,
    assigned_agent: "marketing-agent",
    created_at: "2026-03-01T00:00:00Z",
    updated_at: "2026-03-10T00:00:00Z",
    completed_at: "2026-03-10T00:00:00Z",
  },
  {
    id: "2",
    company_id: "1",
    department_type: DepartmentType.SALES,
    title: "Build outreach sequence for warm leads",
    description: "Create 5-email nurture sequence targeting leads who engaged with demo.",
    status: TaskStatus.IN_PROGRESS,
    priority: TaskPriority.HIGH,
    assigned_agent: "sales-agent",
    created_at: "2026-03-05T00:00:00Z",
    updated_at: "2026-03-11T00:00:00Z",
    completed_at: null,
  },
  {
    id: "3",
    company_id: "1",
    department_type: DepartmentType.PRODUCT,
    title: "Analyze user feedback from beta",
    description: "Compile and categorize all beta user feedback into actionable insights.",
    status: TaskStatus.TODO,
    priority: TaskPriority.MEDIUM,
    assigned_agent: null,
    created_at: "2026-03-08T00:00:00Z",
    updated_at: "2026-03-08T00:00:00Z",
    completed_at: null,
  },
  {
    id: "4",
    company_id: "1",
    department_type: DepartmentType.ENGINEERING,
    title: "Fix authentication timeout bug",
    description: "Users report being logged out after 5 minutes. Investigate and fix.",
    status: TaskStatus.BLOCKED,
    priority: TaskPriority.CRITICAL,
    assigned_agent: "dev-agent",
    created_at: "2026-03-09T00:00:00Z",
    updated_at: "2026-03-11T00:00:00Z",
    completed_at: null,
  },
  {
    id: "5",
    company_id: "1",
    department_type: DepartmentType.CUSTOMER_SUPPORT,
    title: "Set up FAQ knowledge base",
    description: "Create comprehensive FAQ from common support tickets.",
    status: TaskStatus.TODO,
    priority: TaskPriority.LOW,
    assigned_agent: null,
    created_at: "2026-03-10T00:00:00Z",
    updated_at: "2026-03-10T00:00:00Z",
    completed_at: null,
  },
  {
    id: "6",
    company_id: "1",
    department_type: DepartmentType.RESEARCH,
    title: "Competitor pricing analysis",
    description: "Research and document competitor pricing models and positioning.",
    status: TaskStatus.IN_PROGRESS,
    priority: TaskPriority.MEDIUM,
    assigned_agent: "research-agent",
    created_at: "2026-03-07T00:00:00Z",
    updated_at: "2026-03-11T00:00:00Z",
    completed_at: null,
  },
];

const departmentOptions = Object.values(DepartmentType).map((d) => ({
  value: d,
  label: d.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase()),
}));

const priorityOptions = Object.values(TaskPriority).map((p) => ({
  value: p,
  label: p.charAt(0).toUpperCase() + p.slice(1),
}));

export function TaskBoard() {
  const [tasks] = useState<AgentTask[]>(mockTasks);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newDept, setNewDept] = useState(DepartmentType.MARKETING);
  const [newPriority, setNewPriority] = useState(TaskPriority.MEDIUM);

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    // Placeholder - would call createTask API
    setDialogOpen(false);
    setNewTitle("");
    setNewDesc("");
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Task Board</h2>
        <Button onClick={() => setDialogOpen(true)} size="sm">
          <Plus className="h-4 w-4 mr-1" />
          New Task
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {columns.map((col) => {
          const columnTasks = tasks.filter((t) => t.status === col.status);
          return (
            <div key={col.status} className="space-y-3">
              <div className="flex items-center justify-between px-1">
                <h3 className={`text-sm font-medium ${col.color}`}>
                  {col.label}
                </h3>
                <span className="text-xs text-muted-foreground">
                  {columnTasks.length}
                </span>
              </div>
              <div className="space-y-2 min-h-[200px]">
                {columnTasks.map((task) => (
                  <Card
                    key={task.id}
                    className="cursor-pointer hover:border-primary/30 transition-colors"
                  >
                    <CardContent className="p-3">
                      <div className="flex items-start gap-2">
                        <GripVertical className="h-4 w-4 text-muted-foreground/50 mt-0.5 shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium leading-tight">
                            {task.title}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                            {task.description}
                          </p>
                          <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                            <Badge
                              variant={priorityVariant[task.priority]}
                              className="text-[10px] px-1.5 py-0"
                            >
                              {task.priority}
                            </Badge>
                            <Badge
                              variant="outline"
                              className="text-[10px] px-1.5 py-0 capitalize"
                            >
                              {task.department_type.replace("_", " ")}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogHeader>
          <DialogTitle>Create New Task</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleCreate} className="space-y-4 mt-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Title</label>
            <Input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Task title"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Description</label>
            <Textarea
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              placeholder="Describe the task..."
              rows={3}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Department</label>
              <Select
                options={departmentOptions}
                value={newDept}
                onChange={(e) => setNewDept(e.target.value as DepartmentType)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Priority</label>
              <Select
                options={priorityOptions}
                value={newPriority}
                onChange={(e) => setNewPriority(e.target.value as TaskPriority)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Create Task</Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
}
