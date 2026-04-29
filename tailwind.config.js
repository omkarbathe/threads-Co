/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/routes/**/*.py",      // Scans your new route file
    "./app/static/js/**/*.js"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}