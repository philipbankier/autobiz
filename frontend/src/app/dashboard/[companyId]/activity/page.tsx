import { ActivityLog } from "@/components/activity/activity-log";

export default function ActivityPage() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Agent Activity</h2>
        <p className="text-sm text-muted-foreground">
          Real-time log of all agent runs across departments
        </p>
      </div>
      <ActivityLog />
    </div>
  );
}
