"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface DropdownMenuProps {
  children: React.ReactNode;
}

interface DropdownContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const DropdownContext = React.createContext<DropdownContextValue>({
  open: false,
  setOpen: () => {},
});

function DropdownMenu({ children }: DropdownMenuProps) {
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    const handleClick = () => setOpen(false);
    if (open) {
      document.addEventListener("click", handleClick);
      return () => document.removeEventListener("click", handleClick);
    }
  }, [open]);

  return (
    <DropdownContext.Provider value={{ open, setOpen }}>
      <div className="relative inline-block text-left">{children}</div>
    </DropdownContext.Provider>
  );
}

function DropdownMenuTrigger({
  className,
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { open, setOpen } = React.useContext(DropdownContext);
  return (
    <button
      className={cn("", className)}
      onClick={(e) => {
        e.stopPropagation();
        setOpen(!open);
      }}
      {...props}
    >
      {children}
    </button>
  );
}

function DropdownMenuContent({
  className,
  children,
  align = "end",
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { align?: "start" | "end" }) {
  const { open } = React.useContext(DropdownContext);
  if (!open) return null;

  return (
    <div
      className={cn(
        "absolute z-50 mt-2 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md",
        align === "end" ? "right-0" : "left-0",
        className
      )}
      onClick={(e) => e.stopPropagation()}
      {...props}
    >
      {children}
    </div>
  );
}

function DropdownMenuItem({
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { setOpen } = React.useContext(DropdownContext);
  return (
    <button
      className={cn(
        "relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground",
        className
      )}
      onClick={(e) => {
        props.onClick?.(e);
        setOpen(false);
      }}
      {...props}
    />
  );
}

function DropdownMenuSeparator({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("-mx-1 my-1 h-px bg-border", className)} {...props} />;
}

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
};
