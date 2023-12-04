/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    fontFamily: {
      sans: ["DM Sans", "sans-serif"],
      serif: ["DM Serif Display", "serif"],
      mono: ["DM Mono", "monospace"],
    },
    extend: {},
  },
  plugins: [],
};
