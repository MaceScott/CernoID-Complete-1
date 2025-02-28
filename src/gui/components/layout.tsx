import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { Providers } from "@/components/providers/providers"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: {
    default: "CernoID Security",
    template: "%s | CernoID Security",
  },
  description: "Advanced security and surveillance management system",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}

export function generateStaticParams() {
  return []
} 