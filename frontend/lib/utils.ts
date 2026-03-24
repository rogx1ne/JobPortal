import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function moneyRange(min: number | null, max: number | null, currency = "") {
  if (min == null && max == null) return "Not specified";
  const prefix = currency ? `${currency} ` : "";
  if (min != null && max != null && min === max) return `${prefix}${min.toLocaleString()}`;
  if (min != null && max != null) return `${prefix}${min.toLocaleString()} - ${max.toLocaleString()}`;
  if (min != null) return `${prefix}From ${min.toLocaleString()}`;
  return `${prefix}Up to ${max?.toLocaleString()}`;
}

export function readableDate(value: string | null) {
  if (!value) return "Unknown";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return "Unknown";
  return dt.toLocaleDateString();
}

const ENTITY_MAP: Record<string, string> = {
  "&amp;": "&",
  "&lt;": "<",
  "&gt;": ">",
  "&quot;": "\"",
  "&#39;": "'",
  "&nbsp;": " ",
};

export function cleanJobText(value: string | null | undefined) {
  const raw = value ?? "";
  const decoded = Object.entries(ENTITY_MAP).reduce(
    (acc, [entity, replacement]) => acc.split(entity).join(replacement),
    raw,
  );
  return decoded
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}
