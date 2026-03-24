"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AssistantPanel } from "@/components/assistant-panel";
import { Button } from "@/components/ui/button";
import { apiGet, apiPatch } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";
import type { Job, SavedJobRow, UserMe } from "@/lib/types";
import { moneyRange } from "@/lib/utils";

type RecommendationResponse = {
  recommendations: Job[];
};

export default function DashboardPage() {
  const router = useRouter();
  const [authRequired, setAuthRequired] = useState(false);
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileMessage, setProfileMessage] = useState("");
  const [error, setError] = useState("");
  const [me, setMe] = useState<UserMe | null>(null);
  const [savedJobs, setSavedJobs] = useState<SavedJobRow[]>([]);
  const [recommended, setRecommended] = useState<Job[]>([]);
  const [profileForm, setProfileForm] = useState({
    full_name: "",
    headline: "",
    skills: "",
    bio: "",
    resume_url: "",
  });

  useEffect(() => {
    const load = async () => {
      if (!isLoggedIn()) {
        setAuthRequired(true);
        setLoading(false);
        router.replace("/auth/login?next=/dashboard");
        return;
      }
      try {
        const [meData, savedData, recData] = await Promise.all([
          apiGet<UserMe>("/auth/me", { auth: true }),
          apiGet<SavedJobRow[]>("/user/saved", { auth: true }),
          apiGet<RecommendationResponse>("/assistant/recommendations", { auth: true }),
        ]);
        setMe(meData);
        setSavedJobs(savedData);
        setRecommended(recData.recommendations ?? []);
        setProfileForm({
          full_name: meData.profile.full_name ?? "",
          headline: meData.profile.headline ?? "",
          skills: meData.profile.skills ?? "",
          bio: meData.profile.bio ?? "",
          resume_url: meData.profile.resume_url ?? "",
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard.");
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [router]);

  const saveProfile = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSavingProfile(true);
    setProfileMessage("");
    setError("");
    try {
      const updated = await apiPatch<UserMe>("/auth/me", profileForm, { auth: true });
      setMe(updated);
      const recData = await apiGet<RecommendationResponse>("/assistant/recommendations", { auth: true });
      setRecommended(recData.recommendations ?? []);
      setProfileMessage("Profile updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile.");
    } finally {
      setSavingProfile(false);
    }
  };

  if (loading) {
    return <p className="text-sm text-muted">Loading dashboard...</p>;
  }

  if (authRequired) {
    return (
      <section className="surface mx-auto max-w-2xl p-8 text-center">
        <p className="eyebrow">Redirecting</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink">Taking you to login...</h1>
        <p className="mt-2 text-sm text-muted">Dashboard requires authentication.</p>
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <section className="surface p-6">
        <p className="eyebrow">Overview</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink">
          {me?.profile.full_name || me?.username || "Your"} Dashboard
        </h1>
        <p className="mt-2 text-sm text-muted">
          Track your saved opportunities, review AI recommendations, and manage applications.
        </p>
        {error ? <p className="mt-2 text-sm text-[#b12a2a]">{error}</p> : null}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <article className="surface p-5">
          <p className="eyebrow">Profile</p>
          <h2 className="mt-1 text-xl font-semibold text-ink">Improve recommendation quality</h2>
          <form className="mt-4 space-y-3" onSubmit={saveProfile}>
            <input
              value={profileForm.full_name}
              onChange={(event) => setProfileForm((prev) => ({ ...prev, full_name: event.target.value }))}
              placeholder="Full name"
              className="w-full rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
            />
            <input
              value={profileForm.headline}
              onChange={(event) => setProfileForm((prev) => ({ ...prev, headline: event.target.value }))}
              placeholder="Headline (e.g. Backend Engineer Intern)"
              className="w-full rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
            />
            <input
              value={profileForm.skills}
              onChange={(event) => setProfileForm((prev) => ({ ...prev, skills: event.target.value }))}
              placeholder="Skills (comma separated)"
              className="w-full rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
            />
            <textarea
              value={profileForm.bio}
              onChange={(event) => setProfileForm((prev) => ({ ...prev, bio: event.target.value }))}
              rows={3}
              placeholder="Short bio"
              className="w-full rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
            />
            <input
              value={profileForm.resume_url}
              onChange={(event) => setProfileForm((prev) => ({ ...prev, resume_url: event.target.value }))}
              placeholder="Resume URL"
              className="w-full rounded-xl border border-border bg-white/90 px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
            />
            <Button type="submit" disabled={savingProfile}>
              {savingProfile ? "Saving..." : "Save Profile"}
            </Button>
            {profileMessage ? <p className="text-sm text-muted">{profileMessage}</p> : null}
          </form>
        </article>

        <article className="surface p-5">
          <p className="eyebrow">Saved Jobs</p>
          <h2 className="mt-1 text-xl font-semibold text-ink">{savedJobs.length} roles saved</h2>
          <div className="mt-4 space-y-3">
            {savedJobs.length ? (
              savedJobs.slice(0, 8).map((saved) => (
                <div key={saved.id} className="rounded-xl border border-border bg-white/80 p-3">
                  <p className="font-semibold text-ink">{saved.job.title}</p>
                  <p className="text-sm text-muted">
                    {saved.job.company_name} • {saved.job.location || "Remote"}
                  </p>
                  <p className="text-sm text-muted">
                    Salary: {moneyRange(saved.job.salary_min, saved.job.salary_max, saved.job.salary_currency)}
                  </p>
                  <Link className="text-sm font-medium text-accent underline" href={`/jobs/${saved.job.id}`}>
                    Open role
                  </Link>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted">No saved jobs yet. Explore the Jobs page and save a few roles.</p>
            )}
          </div>
        </article>

        <article className="surface p-5">
          <p className="eyebrow">AI Picks</p>
          <h2 className="mt-1 text-xl font-semibold text-ink">Recommended for your profile</h2>
          <div className="mt-4 space-y-3">
            {recommended.length ? (
              recommended.slice(0, 6).map((job) => (
                <div key={job.id} className="rounded-xl border border-border bg-white/80 p-3">
                  <p className="font-semibold text-ink">{job.title}</p>
                  <p className="text-sm text-muted">
                    {job.company_name} • {job.location || "Remote"}
                  </p>
                  <Link className="text-sm font-medium text-accent underline" href={`/jobs/${job.id}`}>
                    View detail
                  </Link>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted">No recommendations yet. Update profile headline and skills first.</p>
            )}
          </div>
        </article>
      </section>

      <AssistantPanel defaultPrompt="Recommend 3 jobs for my profile and suggest resume improvements." />
    </div>
  );
}
