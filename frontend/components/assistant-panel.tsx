"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { apiPost } from "@/lib/api";
import type { AssistantReply } from "@/lib/types";

type AssistantPanelProps = {
  jobId?: number;
  defaultPrompt?: string;
};

export function AssistantPanel({ jobId, defaultPrompt = "" }: AssistantPanelProps) {
  const [message, setMessage] = useState(defaultPrompt);
  const [loading, setLoading] = useState(false);
  const [reply, setReply] = useState<AssistantReply | null>(null);
  const [error, setError] = useState("");

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<AssistantReply>(
        "/assistant/chat",
        { message, job_id: jobId },
        { auth: true },
      );
      setReply(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not get assistant response.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="rounded-2xl border border-border bg-panel p-4">
      <p className="mb-2 font-mono text-xs uppercase tracking-[0.18em] text-muted">Assistant</p>
      <h3 className="text-lg font-semibold text-ink">Ask for recommendations, resume help, or eligibility checks</h3>

      <form className="mt-4 space-y-3" onSubmit={submit}>
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          rows={4}
          placeholder="Example: suggest backend internships in Bengaluru and tell me if I match"
          className="w-full rounded-xl border border-border bg-[#f7fbf4] p-3 text-sm text-ink outline-none ring-accent transition focus:ring-2"
        />
        <div className="flex items-center gap-2">
          <Button type="submit" disabled={loading}>
            {loading ? "Thinking..." : "Ask Assistant"}
          </Button>
          {error ? <p className="text-sm text-[#bc2f2f]">{error}</p> : null}
        </div>
      </form>

      {reply ? (
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 space-y-3 rounded-xl border border-border/80 bg-[#f6fbf2] p-4"
        >
          <p className="text-sm text-muted">
            Intent: <span className="font-medium text-ink">{reply.intent}</span> | Provider: {reply.provider}
          </p>
          <p className="text-sm leading-6 text-ink">{reply.answer}</p>

          {reply.recommended_jobs.length ? (
            <div>
              <p className="mb-2 text-sm font-semibold text-ink">Recommended roles</p>
              <div className="space-y-2">
                {reply.recommended_jobs.slice(0, 3).map((job) => (
                  <div key={job.id} className="rounded-lg border border-border bg-white/80 p-3 text-sm">
                    <p className="font-semibold text-ink">{job.title}</p>
                    <p className="text-muted">{job.company_name} • {job.location || "Remote"}</p>
                    <div className="mt-2 flex gap-2">
                      <Link className="text-accent underline" href={`/jobs/${job.id}`}>In app</Link>
                      <a className="text-accent underline" href={job.source_url} target="_blank" rel="noreferrer">Source</a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {reply.follow_up_questions.length ? (
            <div>
              <p className="mb-1 text-sm font-semibold text-ink">Follow-up ideas</p>
              <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
                {reply.follow_up_questions.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </motion.div>
      ) : null}
    </section>
  );
}
