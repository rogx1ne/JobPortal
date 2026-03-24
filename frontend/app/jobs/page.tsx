"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";

import { JobCard } from "@/components/job-card";
import { Button } from "@/components/ui/button";
import { withQuery } from "@/lib/api";
import type { Job } from "@/lib/types";

type SearchFormState = {
  q: string;
  location: string;
  role: string;
  experience: string;
};

const initialState: SearchFormState = {
  q: "",
  location: "",
  role: "",
  experience: "",
};
const PAGE_SIZE = 8;

export default function JobsPage() {
  const [form, setForm] = useState<SearchFormState>(initialState);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);

  const loadJobs = useCallback(async (state: SearchFormState) => {
    setLoading(true);
    setError("");
    setPage(1);
    try {
      const url = withQuery("/jobs/search", {
        q: state.q,
        location: state.location,
        role: state.role,
        experience: state.experience,
        limit: 96,
      });
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) throw new Error("Unable to load jobs");
      const data = (await res.json()) as Job[];
      setJobs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load jobs.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadJobs(initialState);
  }, [loadJobs]);

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await loadJobs(form);
  };

  const totalPages = Math.max(1, Math.ceil(jobs.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const start = (safePage - 1) * PAGE_SIZE;
  const pageJobs = jobs.slice(start, start + PAGE_SIZE);

  return (
    <div className="space-y-6">
      <section className="surface p-6">
        <p className="eyebrow">Search</p>
        <h1 className="mt-1 text-3xl font-semibold text-ink">Find relevant jobs fast</h1>
        <form className="mt-4 grid gap-3 md:grid-cols-4" onSubmit={onSubmit}>
          <input
            value={form.q}
            onChange={(event) => setForm((curr) => ({ ...curr, q: event.target.value }))}
            placeholder="Keyword"
            className="rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
          />
          <input
            value={form.location}
            onChange={(event) => setForm((curr) => ({ ...curr, location: event.target.value }))}
            placeholder="Location"
            className="rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
          />
          <input
            value={form.role}
            onChange={(event) => setForm((curr) => ({ ...curr, role: event.target.value }))}
            placeholder="Role"
            className="rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
          />
          <div className="flex gap-2">
            <input
              value={form.experience}
              onChange={(event) => setForm((curr) => ({ ...curr, experience: event.target.value }))}
              placeholder="Experience"
              className="w-full rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
            />
            <Button type="submit">Search</Button>
          </div>
        </form>
      </section>

      {error ? <p className="text-sm text-[#b12a2a]">{error}</p> : null}

      <motion.section className="grid gap-4">
        {loading
          ? Array.from({ length: 6 }).map((_, idx) => (
              <div
                key={`skeleton-${idx}`}
                className="surface animate-pulse p-5"
              >
                <div className="h-4 w-2/5 rounded bg-[#d9e7d6]" />
                <div className="mt-3 h-3 w-1/3 rounded bg-[#e1ece0]" />
                <div className="mt-4 h-3 w-full rounded bg-[#e1ece0]" />
                <div className="mt-2 h-3 w-5/6 rounded bg-[#e1ece0]" />
              </div>
            ))
          : null}
        {!loading && !jobs.length ? (
          <div className="surface p-6 text-sm text-muted">No jobs found for the current filters.</div>
        ) : null}
        {pageJobs.map((job) => (
          <JobCard key={job.id} job={job} />
        ))}
      </motion.section>

      {!loading && jobs.length > PAGE_SIZE ? (
        <section className="surface flex flex-wrap items-center justify-between gap-3 p-4">
          <p className="text-sm text-muted">
            Showing {start + 1}-{Math.min(start + PAGE_SIZE, jobs.length)} of {jobs.length}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="subtle"
              size="sm"
              disabled={safePage <= 1}
              onClick={() => setPage((curr) => Math.max(1, curr - 1))}
            >
              Previous
            </Button>
            <p className="text-sm text-muted">
              Page {safePage} / {totalPages}
            </p>
            <Button
              variant="subtle"
              size="sm"
              disabled={safePage >= totalPages}
              onClick={() => setPage((curr) => Math.min(totalPages, curr + 1))}
            >
              Next
            </Button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
