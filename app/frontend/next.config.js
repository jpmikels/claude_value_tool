/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  
  // Optional: Configure environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080',
  },
  
  // Optional: Disable TypeScript/ESLint errors blocking build (for development)
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
}

module.exports = nextConfig
