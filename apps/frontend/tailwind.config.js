/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        white: '#FFFFFF',
        cream: '#FFF1E7',
        'light-blue': '#B5D2E6',
        'deep-blue': {
          DEFAULT: '#326080',
          dark: '#28506A',
        },
        brown: {
          DEFAULT: '#805232',
          dark: '#6A4229',
        },
        'info-bg': '#B5D2E6',
        danger: '#B3261E',
        success: '#1B7A3D',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
      },
      boxShadow: {
        sm: '0 1px 2px 0 rgb(50 96 128 / 0.08)',
        md: '0 4px 12px -2px rgb(50 96 128 / 0.15)',
        lg: '0 12px 32px -8px rgb(50 96 128 / 0.25)',
      },
    },
  },
  plugins: [],
}
