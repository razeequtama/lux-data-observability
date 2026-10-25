/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        lux: {
          50: '#FAF5FF',
          100: '#F3E8FF',
          200: '#E9D5FF',
          300: '#D8B4FE',
          400: '#C084FC',
          500: '#A855F7',
          600: '#7C3AED', // hover
          700: '#6B46C1', // primary brand
          800: '#553C9A', // active
          900: '#44337A',
          950: '#2E1065',
        },
        slate: {
          950: '#0F172A', // dark canvas
          900: '#1E293B', // card dark
          800: '#334155', // border dark
        },
        status: {
          healthy: '#10B981',
          warning: '#F59E0B',
          corrupted: '#F43F5E',
          neutral: '#64748B',
        },
      },
      fontFamily: {
        sans: [
          'Plus Jakarta Sans',
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
        mono: [
          'JetBrains Mono',
          'Fira Code',
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'Monaco',
          'Consolas',
          'monospace',
        ],
      },
    },
  },
  plugins: [],
};
