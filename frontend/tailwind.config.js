/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bitcoin-orange': '#f7931a',
        'bitcoin-dark': '#111827',
      },
    },
  },
  plugins: [],
}
