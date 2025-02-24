"use client"

import { AuthProvider } from "./auth-provider"
import { ThemeProvider } from "./theme-provider"
import { WebSocketProvider } from "@/lib/websocket"

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <AuthProvider>
        <WebSocketProvider>
          {children}
        </WebSocketProvider>
      </AuthProvider>
    </ThemeProvider>
  )
} 