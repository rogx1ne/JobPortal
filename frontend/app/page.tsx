"use client";

import Link from "next/link";
import { motion } from "framer-motion";

import { Button } from "@/components/ui/button";

const highlights = [
  "Aggregated jobs from compliant public sources",
  "Hybrid ranking (semantic + lexical + recency)",
  "AI assistant for discovery, eligibility, and resume improvements",
];

export default function HomePage() {
  return (
    <div className="space-y-8">
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="surface overflow-hidden p-8 sm:p-10"
      >
        <p className="eyebrow">Job Discovery Engine</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-semibold leading-tight text-ink sm:text-5xl">
          A focused search platform for internships and jobs with reliable source attribution.
        </h1>
        <p className="mt-4 max-w-3xl text-base text-muted sm:text-lg">
          Browse active opportunities, save and track applications, and ask an assistant to prioritize the next best opportunities for your profile.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <Button asChild size="lg">
            <Link href="/jobs">Start Searching</Link>
          </Button>
          <Button variant="subtle" size="lg" asChild>
            <Link href="/dashboard">Open Dashboard</Link>
          </Button>
        </div>
      </motion.section>

      <section className="grid gap-4 md:grid-cols-3">
        {highlights.map((item, index) => (
          <motion.div
            key={item}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08 }}
            className="surface p-5"
          >
            <p className="font-mono text-xs uppercase tracking-[0.2em] text-accent-2">0{index + 1}</p>
            <p className="mt-2 text-base text-ink">{item}</p>
          </motion.div>
        ))}
      </section>
    </div>
  );
}
