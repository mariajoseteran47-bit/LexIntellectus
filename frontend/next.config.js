/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    // Proxy API requests to backend
    // In Docker: BACKEND_INTERNAL_URL=http://backend:8000
    // Locally: defaults to http://localhost:8000
    async rewrites() {
        const backendUrl = process.env.BACKEND_INTERNAL_URL || 'http://backend:8000';
        return [
            {
                source: '/api/:path*',
                destination: `${backendUrl}/api/:path*`,
            },
        ];
    },
};

module.exports = nextConfig;
