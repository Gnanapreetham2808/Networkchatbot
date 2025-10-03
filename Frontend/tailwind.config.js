/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/app/**/*.{js,ts,jsx,tsx}',
    './src/components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif']
      },
      colors: {
        brand: {
          DEFAULT: '#000000',
          subtle: '#111111'
        }
      },
      borderRadius: {
        xl: '1.25rem'
      },
      boxShadow: {
        brand: '0 4px 24px -4px rgba(0,0,0,0.08)'
      },
      backgroundImage: {
        'dot-grid': 'radial-gradient(circle at 1px 1px,#e5e7eb 1px,transparent 0)',
        'hero-fade': 'linear-gradient(to bottom,rgba(255,255,255,1),rgba(255,255,255,0.85),rgba(255,255,255,0))',
        'hero-fade-dark': 'linear-gradient(to bottom,rgba(3,7,18,1),rgba(3,7,18,0.92),rgba(3,7,18,0))'
      }
    },
  },
  plugins: [],
}
