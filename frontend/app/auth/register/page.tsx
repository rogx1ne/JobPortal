"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { apiPost } from "@/lib/api";
import { setSession } from "@/lib/auth";

type TokenPair = {
  access: string;
  refresh: string;
};

export default function RegisterPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await apiPost("/auth/register", form);
      const token = await apiPost<TokenPair>("/auth/login", {
        username: form.username,
        password: form.password,
      });
      setSession(token.access, token.refresh);
      const nextPath = searchParams.get("next") || "/dashboard";
      router.push(nextPath);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mx-auto w-full max-w-lg">
      <div className="surface p-7">
        <p className="eyebrow">Create Account</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink">Start your job search profile</h1>

        <form className="mt-5 space-y-3" onSubmit={onSubmit}>
          <input
            value={form.username}
            onChange={(event) => setForm((prev) => ({ ...prev, username: event.target.value }))}
            placeholder="Username"
            className="w-full rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
            required
          />
          <input
            value={form.email}
            onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
            placeholder="Email"
            type="email"
            className="w-full rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
            required
          />
          <input
            value={form.password}
            onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
            placeholder="Password"
            type="password"
            className="w-full rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
            required
          />
          <Button className="w-full" type="submit" disabled={submitting}>
            {submitting ? "Creating..." : "Create Account"}
          </Button>
          {error ? <p className="text-sm text-[#b12626]">{error}</p> : null}
        </form>

        <p className="mt-4 text-sm text-muted">
          Already have an account?{" "}
          <Link className="font-medium text-accent underline" href="/auth/login">
            Sign in
          </Link>
        </p>
      </div>
    </section>
  );
}
