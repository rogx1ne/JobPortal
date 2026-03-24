"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { apiPost } from "@/lib/api";
import type { Job } from "@/lib/types";
import { cleanJobText, moneyRange, readableDate } from "@/lib/utils";

type JobCardProps = {
  job: Job;
};

export function JobCard({ job }: JobCardProps) {
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string>("");

  const saveJob = async () => {
    setSaving(true);
    setStatus("");
    try {
      await apiPost("/jobs/save", { job_id: job.id }, { auth: true });
      setStatus("Saved");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <motion.article
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="rounded-2xl border border-border bg-panel p-5 shadow-panel"
    >
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-ink">{job.title}</h3>
          <p className="text-sm text-muted">{job.company_name || "Unknown company"}</p>
        </div>
        <p className="rounded-full border border-border px-3 py-1 font-mono text-xs uppercase text-muted">
          {job.role || "General"}
        </p>
      </div>

      <p className="mb-4 line-clamp-3 text-sm text-[#1f2d27]">
        {cleanJobText(job.description_snippet) || "No summary provided."}
      </p>

      <div className="mb-4 grid grid-cols-1 gap-2 text-sm text-muted sm:grid-cols-2">
        <p>Location: {job.location || "Remote / Flexible"}</p>
        <p>Experience: {job.experience || "Not specified"}</p>
        <p>Salary: {moneyRange(job.salary_min, job.salary_max, job.salary_currency)}</p>
        <p>Posted: {readableDate(job.posted_at)}</p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" asChild>
          <Link href={`/jobs/${job.id}`}>View Details</Link>
        </Button>
        <Button size="sm" variant="subtle" onClick={saveJob} disabled={saving}>
          {saving ? "Saving..." : "Save"}
        </Button>
        <Button size="sm" variant="ghost" asChild>
          <a href={job.source_url} target="_blank" rel="noreferrer">
            Open Source
          </a>
        </Button>
        {status ? <span className="text-xs text-muted">{status}</span> : null}
      </div>
    </motion.article>
  );
}
