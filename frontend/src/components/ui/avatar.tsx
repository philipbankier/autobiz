import * as React from "react";
import { cn } from "@/lib/utils";

interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  fallback?: string;
  src?: string;
}

function Avatar({ className, fallback, src, ...props }: AvatarProps) {
  return (
    <div
      className={cn(
        "relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full bg-muted items-center justify-center",
        className
      )}
      {...props}
    >
      {src ? (
        <img src={src} alt="" className="aspect-square h-full w-full object-cover" />
      ) : (
        <span className="text-sm font-medium text-muted-foreground">
          {fallback || "?"}
        </span>
      )}
    </div>
  );
}

export { Avatar };
