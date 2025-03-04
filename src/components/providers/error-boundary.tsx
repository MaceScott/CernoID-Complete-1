"use client"

import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface ErrorBoundaryProps {
  error: Error & { digest?: string }
  reset: () => void
  level?: "layout" | "page" | "component"
}

export default function ErrorBoundary({
  error,
  reset,
  level = "page"
}: ErrorBoundaryProps) {
  useEffect(() => {
    // Log to error reporting service
    console.error(`${level} level error:`, error)
  }, [error, level])

  return (
    <div className={cn(
      "flex items-center justify-center",
      level === "layout" ? "min-h-screen" : "h-full min-h-[400px]",
      "bg-background"
    )}>
      <div className="text-center">
        <div className="mb-4 rounded-full bg-red-100 p-3 dark:bg-red-900/30">
          <AlertCircle className="h-6 w-6 text-red-600 dark:text-red-400" />
        </div>
        <h2 className="mb-2 text-2xl font-semibold text-foreground">
          {level === "layout" ? "Application Error" : "Something went wrong"}
        </h2>
        <p className="mb-4 text-muted-foreground">
          {error.message || "An unexpected error occurred"}
        </p>
        <div className="space-x-2">
          <Button
            onClick={() => window.location.reload()}
            variant="outline"
          >
            Refresh Page
          </Button>
          <Button onClick={reset}>
            Try Again
          </Button>
        </div>
      </div>
    </div>
  )
} 