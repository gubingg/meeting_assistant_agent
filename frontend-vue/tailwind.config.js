/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        ink: '#10212b',
        paper: '#f4efe6',
        sand: '#e5d5c0',
        accent: '#c96f3b',
        pine: '#35524a',
      },
      fontFamily: {
        sans: ['Noto Sans SC', 'PingFang SC', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 18px 40px rgba(16, 33, 43, 0.08)',
      },
    },
  },
  plugins: [],
};
