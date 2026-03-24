import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        bg: "hsl(var(--bg))",
        ink: "hsl(var(--ink))",
        muted: "hsl(var(--muted))",
        panel: "hsl(var(--panel))",
        accent: "hsl(var(--accent))",
        "accent-2": "hsl(var(--accent-2))",
        border: "hsl(var(--border))"
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem"
      },
      boxShadow: {
        panel: "0 20px 70px rgba(14, 34, 24, 0.12)",
      }
    }
  },
  plugins: [],
};

export default config;
