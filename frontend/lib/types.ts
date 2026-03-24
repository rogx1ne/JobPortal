export type Job = {
  id: number;
  title: string;
  company_name: string;
  location: string;
  role: string;
  experience: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  description_snippet: string;
  source: string;
  source_url: string;
  posted_at: string | null;
};

export type UserProfile = {
  full_name: string;
  headline: string;
  bio: string;
  skills: string;
  resume_url: string;
};

export type UserMe = {
  id: number;
  username: string;
  email: string;
  profile: UserProfile;
};

export type SavedJobRow = {
  id: number;
  created_at: string;
  job: Job;
};

export type AssistantReply = {
  intent: string;
  provider: string;
  answer: string;
  recommended_jobs: Array<{
    id: number;
    title: string;
    company_name: string;
    location: string;
    role: string;
    experience: string;
    salary_min: number | null;
    salary_max: number | null;
    source_url: string;
    posted_at: string | null;
  }>;
  follow_up_questions: string[];
};
