/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"SFMono-Regular"', '"Cascadia Code"', 'Consolas', 'monospace'],
      },
      colors: {
        ink: "#030406",
        panel: "#08090c",
        line: "rgba(255,255,255,0.15)",
      },
      boxShadow: {
        quiet: "0 0 70px rgba(255,255,255,0.045)",
      },
    },
  },
  plugins: [],
};
