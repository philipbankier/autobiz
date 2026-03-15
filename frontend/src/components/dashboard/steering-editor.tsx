"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { getSteeringFile, updateSteeringFile } from "@/lib/api";

interface SteeringEditorProps {
  companyId: string;
}

export function SteeringEditor({ companyId }: SteeringEditorProps) {
  const [content, setContent] = useState("");
  const [savedContent, setSavedContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [collapsed, setCollapsed] = useState(true);
  const [preview, setPreview] = useState(false);

  useEffect(() => {
    getSteeringFile(companyId).then((res) => {
      const text = res.data?.content || "";
      setContent(text);
      setSavedContent(text);
      setLoading(false);
    });
  }, [companyId]);

  const isDirty = content !== savedContent;

  async function handleSave() {
    setSaving(true);
    const res = await updateSteeringFile(companyId, content);
    if (res.data) {
      setSavedContent(content);
    }
    setSaving(false);
  }

  return (
    <Card className="bg-gray-900 border-gray-800 h-full flex flex-col">
      {/* Header */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between p-4 border-b border-gray-800 w-full text-left hover:bg-gray-800/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm">{collapsed ? "▸" : "▾"}</span>
          <h3 className="text-sm font-medium text-white">STEERING.md</h3>
          {isDirty && <span className="w-2 h-2 rounded-full bg-amber-500" />}
        </div>
        <span className="text-gray-600 text-xs">Human overrides</span>
      </button>

      {!collapsed && (
        <div className="p-4 flex-1 flex flex-col gap-3">
          {loading ? (
            <p className="text-gray-500 text-sm">Loading...</p>
          ) : (
            <>
              {/* Toggle */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPreview(false)}
                  className={`text-xs px-2 py-1 rounded ${
                    !preview ? "bg-gray-800 text-white" : "text-gray-500 hover:text-gray-300"
                  }`}
                >
                  Edit
                </button>
                <button
                  onClick={() => setPreview(true)}
                  className={`text-xs px-2 py-1 rounded ${
                    preview ? "bg-gray-800 text-white" : "text-gray-500 hover:text-gray-300"
                  }`}
                >
                  Preview
                </button>
              </div>

              {preview ? (
                <div className="flex-1 min-h-[200px] overflow-y-auto rounded-md border border-gray-800 p-3">
                  <pre className="text-gray-300 text-sm whitespace-pre-wrap font-mono">{content || "(empty)"}</pre>
                </div>
              ) : (
                <Textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="# STEERING.md&#10;Add human overrides and instructions here..."
                  className="flex-1 min-h-[200px] bg-gray-950 border-gray-800 text-gray-300 font-mono text-sm resize-y"
                />
              )}

              <div className="flex items-center justify-between">
                <span className="text-gray-600 text-xs">
                  {isDirty ? "Unsaved changes" : "Saved"}
                </span>
                <Button
                  size="sm"
                  disabled={!isDirty || saving}
                  onClick={handleSave}
                  className="text-xs h-7"
                >
                  {saving ? "Saving..." : "Save"}
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </Card>
  );
}
