"use client"

import { AuthProvider } from './AuthProvider'
import { ThemeProvider } from './ThemeProvider'
import { WebSocketProvider } from './WebSocketProvider'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <WebSocketProvider>
          {children}
        </WebSocketProvider>
      </AuthProvider>
    </ThemeProvider>
  )
} 