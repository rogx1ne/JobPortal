import { notFound } from "next/navigation";

import { JobActions } from "@/components/job-actions";
import type { Job } from "@/lib/types";
import { cleanJobText, moneyRange, readableDate } from "@/lib/utils";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api";

async function getJob(id: string): Promise<Job | null> {
  const res = await fetch(`${API_BASE_URL}/jobs/${id}`, { cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as Job;
}

export default async function JobDetailPage({ params }: { params: { id: string } }) {
  const job = await getJob(params.id);
  if (!job) notFound();

  return (
    <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
      <article className="surface p-6">
        <p className="eyebrow">Job Detail</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink">{job.title}</h1>
        <p className="text-muted">{job.company_name || "Unknown company"}</p>

        <div className="mt-5 grid gap-2 text-sm text-muted sm:grid-cols-2">
          <p>Location: {job.location || "Remote / Flexible"}</p>
          <p>Role: {job.role || "General"}</p>
          <p>Experience: {job.experience || "Not specified"}</p>
          <p>Salary: {moneyRange(job.salary_min, job.salary_max, job.salary_currency)}</p>
          <p>Posted: {readableDate(job.posted_at)}</p>
          <p>Source: {job.source || "Aggregated"}</p>
        </div>

        <p className="mt-6 text-sm leading-7 text-ink">
          {cleanJobText(job.description_snippet) || "No description available."}
        </p>

        <a
          href={job.source_url}
          target="_blank"
          rel="noreferrer"
          className="mt-6 inline-block text-sm font-medium text-accent underline"
        >
          View Original Listing
        </a>
      </article>

      <aside>
        <JobActions jobId={job.id} jobTitle={job.title} />
      </aside>
    </div>
  );
}
