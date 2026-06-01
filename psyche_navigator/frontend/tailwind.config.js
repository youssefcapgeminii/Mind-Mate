/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        serif: ['"DM Serif Display"', 'Georgia', 'serif'],
        sans:  ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        forest: {
          50:  '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#25D366',  // WhatsApp bright green
          500: '#00A884',  // WhatsApp teal
          600: '#008069',
          700: '#005C4B',
          800: '#003D31',
          900: '#1d2c24',
          950: '#111B21',
        },
        warm: {
          50:  '#F0F2F5',  // main background
          100: '#FFFFFF',  // panel / card surface
          200: '#E9EDEF',  // border / divider
          300: '#D1D7DB',  // stronger border
          400: '#667781',  // muted icons
          500: '#667781',  // secondary text
          600: '#54656F',  // readable muted text
          700: '#3B4A54',
          800: '#202C33',
          900: '#111B21',  // primary text
        },
        copper: {
          400: '#d4864a',
          500: '#c07038',
          600: '#a85e2a',
        },
      },
      boxShadow: {
        'warm-sm': '0 1px 3px 0 rgba(0,0,0,0.08), 0 1px 2px -1px rgba(0,0,0,0.06)',
        'warm-md': '0 4px 12px -2px rgba(0,0,0,0.10), 0 2px 6px -2px rgba(0,0,0,0.06)',
        'warm-lg': '0 12px 32px -4px rgba(0,0,0,0.12), 0 4px 12px -4px rgba(0,0,0,0.08)',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}
