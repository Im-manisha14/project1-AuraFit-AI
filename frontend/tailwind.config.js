module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // AuraFit Brand Colors
        aura: {
          lavender: '#B8A1D9',     // Main Brand Color
          plum: '#4B2E83',         // Accent/Buttons
          ivory: '#F7F4EF',        // Background
          blush: '#F2C6CC',        // Highlights
          charcoal: '#333333',     // Primary Text
          taupe: '#A89F91',        // Borders/Secondary
        },
        primary: '#4B2E83',        // Deep Plum for primary elements
        secondary: '#B8A1D9',      // Soft Lavender for secondary
        accent: '#F2C6CC',         // Blush Pink for accents
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'aura-gradient': 'linear-gradient(135deg, #B8A1D9 0%, #F2C6CC 100%)',
        'aura-dark': 'linear-gradient(135deg, #4B2E83 0%, #B8A1D9 100%)',
      }
    },
  },
  plugins: [],
}
