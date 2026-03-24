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

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const data = await apiPost<TokenPair>("/auth/login", { username, password });
      setSession(data.access, data.refresh);
      const nextPath = searchParams.get("next") || "/dashboard";
      router.push(nextPath);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mx-auto w-full max-w-lg">
      <div className="surface p-7">
        <p className="eyebrow">Welcome Back</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink">Sign in to your account</h1>

        <form className="mt-5 space-y-3" onSubmit={onSubmit}>
          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Username"
            className="w-full rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
            required
          />
          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password"
            type="password"
            className="w-full rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
            required
          />
          <Button className="w-full" type="submit" disabled={submitting}>
            {submitting ? "Signing in..." : "Sign In"}
          </Button>
          {error ? <p className="text-sm text-[#b12626]">{error}</p> : null}
        </form>

        <p className="mt-4 text-sm text-muted">
          No account yet?{" "}
          <Link className="font-medium text-accent underline" href="/auth/register">
            Create one
          </Link>
        </p>
      </div>
    </section>
  );
}
