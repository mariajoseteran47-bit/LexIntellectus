/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                // Design System: "Minimalismo Judicial"
                primary: {
                    50: '#eef3f9',
                    100: '#d4e0ed',
                    200: '#a9c1db',
                    300: '#7ea2c9',
                    400: '#4f7fb0',
                    500: '#1E3A5F', // Azul Justicia - Primary
                    600: '#1a3253',
                    700: '#152a46',
                    800: '#11213a',
                    900: '#0d192d',
                },
                accent: {
                    50: '#fdf8eb',
                    100: '#f9edc6',
                    200: '#f0d88a',
                    300: '#e6c34e',
                    400: '#D4AF37', // Dorado Notarial - Secondary
                    500: '#c4a030',
                    600: '#a88829',
                    700: '#8c7022',
                    800: '#70581b',
                    900: '#544114',
                },
                success: {
                    400: '#4ade80',
                    500: '#22c55e',
                },
                warning: {
                    400: '#fb923c',
                    500: '#f97316',
                },
                danger: {
                    400: '#f87171',
                    500: '#ef4444',
                },
                // Neutral grays for judicial feel
                surface: {
                    50: '#fafafa',
                    100: '#f5f5f5',
                    200: '#e5e5e5',
                    300: '#d4d4d4',
                    400: '#a3a3a3',
                    500: '#737373',
                    600: '#525252',
                    700: '#404040',
                    800: '#262626',
                    900: '#171717',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
                mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
            },
            boxShadow: {
                'judicial': '0 1px 3px rgba(30, 58, 95, 0.08), 0 1px 2px rgba(30, 58, 95, 0.06)',
                'judicial-md': '0 4px 6px rgba(30, 58, 95, 0.07), 0 2px 4px rgba(30, 58, 95, 0.06)',
                'judicial-lg': '0 10px 15px rgba(30, 58, 95, 0.1), 0 4px 6px rgba(30, 58, 95, 0.05)',
                'gold-glow': '0 0 20px rgba(212, 175, 55, 0.15)',
            },
            backgroundImage: {
                'gradient-judicial': 'linear-gradient(135deg, #1E3A5F 0%, #2d5a8e 50%, #1E3A5F 100%)',
                'gradient-gold': 'linear-gradient(135deg, #D4AF37 0%, #e6c34e 50%, #D4AF37 100%)',
            },
            animation: {
                'fade-in': 'fadeIn 0.5s ease-in-out',
                'slide-up': 'slideUp 0.3s ease-out',
                'pulse-gold': 'pulseGold 2s ease-in-out infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(10px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                pulseGold: {
                    '0%, 100%': { boxShadow: '0 0 0 0 rgba(212, 175, 55, 0.2)' },
                    '50%': { boxShadow: '0 0 0 8px rgba(212, 175, 55, 0)' },
                },
            },
        },
    },
    plugins: [],
};
