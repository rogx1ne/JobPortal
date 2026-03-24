"use client";

import { useState } from "react";

import { AssistantPanel } from "@/components/assistant-panel";
import { Button } from "@/components/ui/button";
import { apiPost } from "@/lib/api";

type JobActionsProps = {
  jobId: number;
  jobTitle: string;
};

export function JobActions({ jobId, jobTitle }: JobActionsProps) {
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState<"save" | "apply" | "">("");

  const save = async () => {
    setLoading("save");
    setStatus("");
    try {
      await apiPost("/jobs/save", { job_id: jobId }, { auth: true });
      setStatus("Saved to dashboard.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Save failed.");
    } finally {
      setLoading("");
    }
  };

  const apply = async () => {
    setLoading("apply");
    setStatus("");
    try {
      await apiPost("/jobs/apply", { job_id: jobId, status: "applied" }, { auth: true });
      setStatus("Application tracked.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Apply failed.");
    } finally {
      setLoading("");
    }
  };

  return (
    <div className="space-y-4">
      <section className="rounded-2xl border border-border bg-panel p-4">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-muted">Actions</p>
        <h3 className="mb-3 mt-1 text-lg font-semibold text-ink">Manage this role</h3>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="subtle" onClick={save} disabled={loading !== ""}>
            {loading === "save" ? "Saving..." : "Save Job"}
          </Button>
          <Button onClick={apply} disabled={loading !== ""}>
            {loading === "apply" ? "Updating..." : "Mark Applied"}
          </Button>
        </div>
        {status ? <p className="mt-2 text-sm text-muted">{status}</p> : null}
      </section>

      <AssistantPanel jobId={jobId} defaultPrompt={`Can you check if I am eligible for this role: ${jobTitle}`} />
    </div>
  );
}
