import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1d1d1f",
        subink: "#6e6e73",
        faint: "#86868b",
        canvas: "#fbfbfd",
        surface: "#ffffff",
        hairline: "#d2d2d7",
        hairlinesoft: "rgba(0,0,0,0.08)",
        accent: {
          DEFAULT: "#0071e3",
          hover: "#0077ed",
          soft: "#e8f2ff",
        },
        success: "#2fa64b",
        warn: "#ff9500",
        danger: "#ff3b30",
      },
      fontFamily: {
        display: [
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Display",
          "SF Pro Text",
          "Inter",
          "Segoe UI",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        text: [
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Text",
          "Inter",
          "Segoe UI",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: ["SF Mono", "ui-monospace", "Menlo", "Consolas", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,0.04), 0 8px 24px -8px rgba(0,0,0,0.08)",
        cardhover: "0 2px 6px rgba(0,0,0,0.06), 0 16px 40px -12px rgba(0,0,0,0.14)",
        pop: "0 20px 60px -15px rgba(0,113,227,0.35)",
      },
      borderRadius: {
        xl2: "1.25rem",
        xl3: "1.75rem",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0" },
        },
        ringspin: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
      animation: {
        fadeUp: "fadeUp 0.5s cubic-bezier(0.16,1,0.3,1) both",
        shimmer: "shimmer 1.6s linear infinite",
        ringspin: "ringspin 0.9s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
