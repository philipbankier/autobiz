import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  DollarSign,
  TrendingUp,
  ListTodo,
  Bot,
  Cpu,
  Clock,
} from "lucide-react";

const metrics = [
  {
    label: "Total Revenue",
    value: "$12,450",
    change: "+12.5%",
    icon: DollarSign,
    trend: "up",
  },
  {
    label: "AI Costs (MTD)",
    value: "$342.18",
    change: "+3.2%",
    icon: TrendingUp,
    trend: "up",
  },
  {
    label: "Active Tasks",
    value: "24",
    change: "-2",
    icon: ListTodo,
    trend: "down",
  },
  {
    label: "Active Departments",
    value: "6",
    change: "0",
    icon: Bot,
    trend: "neutral",
  },
];

const recentActivity = [
  {
    dept: "Marketing",
    action: "Published 3 blog posts",
    time: "12 min ago",
  },
  {
    dept: "Sales",
    action: "Sent 15 outreach emails",
    time: "28 min ago",
  },
  {
    dept: "Support",
    action: "Resolved 8 tickets",
    time: "1 hr ago",
  },
  {
    dept: "Research",
    action: "Completed competitor analysis",
    time: "2 hrs ago",
  },
  {
    dept: "Product",
    action: "Updated feature roadmap",
    time: "3 hrs ago",
  },
];

export default function CompanyOverviewPage() {
  return (
    <div className="space-y-6">
      {/* Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <Card key={metric.label}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {metric.label}
                </CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metric.value}</div>
                <p
                  className={`text-xs mt-1 ${
                    metric.trend === "up"
                      ? "text-emerald-500"
                      : metric.trend === "down"
                      ? "text-red-500"
                      : "text-muted-foreground"
                  }`}
                >
                  {metric.change} from last month
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-sm"
                >
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="text-xs w-24 justify-center">
                      {item.dept}
                    </Badge>
                    <span>{item.action}</span>
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap ml-4">
                    {item.time}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Department Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-4 w-4" />
              Department Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { name: "Marketing", status: "active", tasks: 5, cost: "$45.20" },
                { name: "Sales", status: "active", tasks: 8, cost: "$62.10" },
                { name: "Customer Support", status: "active", tasks: 3, cost: "$89.50" },
                { name: "Product", status: "active", tasks: 4, cost: "$31.00" },
                { name: "Engineering", status: "paused", tasks: 2, cost: "$78.38" },
                { name: "Research", status: "active", tasks: 2, cost: "$36.00" },
              ].map((dept) => (
                <div
                  key={dept.name}
                  className="flex items-center justify-between text-sm"
                >
                  <div className="flex items-center gap-3">
                    <Badge
                      variant={dept.status === "active" ? "success" : "warning"}
                      className="text-xs w-16 justify-center"
                    >
                      {dept.status}
                    </Badge>
                    <span className="font-medium">{dept.name}</span>
                  </div>
                  <div className="flex items-center gap-4 text-muted-foreground">
                    <span className="text-xs">{dept.tasks} tasks</span>
                    <span className="text-xs w-16 text-right">{dept.cost}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
