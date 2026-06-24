/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          900: "#1e3a5f",
        },
        status: {
          created: "#22c55e",
          pending: "#eab308",
          awaiting: "#f97316",
          failed: "#ef4444",
          cancelled: "#6b7280",
        },
      },
    },
  },
  plugins: [],
};
