import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
  weight: ['300', '400', '500', '600', '700', '800', '900'],
})

export const metadata: Metadata = {
  title: 'CrisisMesh AI — Emergency Operations Center',
  description: 'Real-time AI-powered disaster response and emergency management platform',
  keywords: ['disaster response', 'emergency management', 'AI', 'real-time', 'crisis management'],
  authors: [{ name: 'CrisisMesh Team' }],
  openGraph: {
    title: 'CrisisMesh AI — Emergency Operations Center',
    description: 'Real-time AI-powered disaster response and emergency management platform',
    type: 'website',
  },
  icons: {
    icon: 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🚨</text></svg>',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans bg-bg-primary text-text-primary antialiased">
        {children}
      </body>
    </html>
  )
}
