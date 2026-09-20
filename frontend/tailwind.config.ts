import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Background palette
        'bg-primary': '#0a0f1e',
        'bg-secondary': '#0d1425',
        'bg-card': '#111827',
        'bg-card-hover': '#1a2235',
        'bg-border': '#1e2d45',
        // Accent colors
        'accent-red': '#ff2d55',
        'accent-orange': '#ff9f0a',
        'accent-green': '#30d158',
        'accent-blue': '#0a84ff',
        'accent-purple': '#bf5af2',
        'accent-cyan': '#32ade6',
        // Text
        'text-primary': '#f5f5f7',
        'text-secondary': '#8e8e93',
        'text-dim': '#48484a',
        // Severity
        'severity-critical': '#ff2d55',
        'severity-warning': '#ff9f0a',
        'severity-normal': '#30d158',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-fast': 'pulse 0.8s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'blink': 'blink 1s step-start infinite',
        'blink-slow': 'blink 2s step-start infinite',
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
        'glow-pulse-red': 'glow-pulse-red 1.5s ease-in-out infinite',
        'slide-in-left': 'slide-in-left 0.3s ease-out',
        'slide-in-up': 'slide-in-up 0.3s ease-out',
        'fade-in': 'fade-in 0.2s ease-out',
        'counter-spin': 'spin 0.5s ease-out',
        'scan': 'scan 3s linear infinite',
        'radar': 'radar 2s linear infinite',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        'glow-pulse': {
          '0%, 100%': {
            boxShadow: '0 0 5px rgba(10, 132, 255, 0.3), 0 0 20px rgba(10, 132, 255, 0.1)',
          },
          '50%': {
            boxShadow: '0 0 15px rgba(10, 132, 255, 0.6), 0 0 40px rgba(10, 132, 255, 0.2)',
          },
        },
        'glow-pulse-red': {
          '0%, 100%': {
            boxShadow: '0 0 5px rgba(255, 45, 85, 0.4), 0 0 20px rgba(255, 45, 85, 0.15)',
          },
          '50%': {
            boxShadow: '0 0 20px rgba(255, 45, 85, 0.8), 0 0 50px rgba(255, 45, 85, 0.3)',
          },
        },
        'slide-in-left': {
          '0%': { transform: 'translateX(-20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        'slide-in-up': {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        radar: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
      boxShadow: {
        'glow-red': '0 0 20px rgba(255, 45, 85, 0.4), 0 0 60px rgba(255, 45, 85, 0.1)',
        'glow-orange': '0 0 20px rgba(255, 159, 10, 0.4), 0 0 60px rgba(255, 159, 10, 0.1)',
        'glow-green': '0 0 20px rgba(48, 209, 88, 0.4), 0 0 60px rgba(48, 209, 88, 0.1)',
        'glow-blue': '0 0 20px rgba(10, 132, 255, 0.4), 0 0 60px rgba(10, 132, 255, 0.1)',
        'card': '0 4px 24px rgba(0, 0, 0, 0.4)',
        'inner-glow': 'inset 0 1px 0 rgba(255,255,255,0.05)',
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(rgba(10, 132, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(10, 132, 255, 0.03) 1px, transparent 1px)",
        'radial-glow': 'radial-gradient(ellipse at center, rgba(10, 132, 255, 0.05) 0%, transparent 70%)',
      },
      backgroundSize: {
        'grid': '40px 40px',
      },
    },
  },
  plugins: [],
}
export default config
