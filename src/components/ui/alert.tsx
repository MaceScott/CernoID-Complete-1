import { AlertCircle, CheckCircle, Info, XCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface AlertProps {
  variant?: "default" | "success" | "error" | "warning" | "info"
  title?: string
  children: React.ReactNode
  className?: string
}

export function Alert({
  variant = "default",
  title,
  children,
  className,
}: AlertProps) {
  const icons = {
    default: Info,
    info: Info,
    success: CheckCircle,
    error: XCircle,
    warning: AlertCircle,
  }

  const Icon = icons[variant]

  return (
    <div
      className={cn(
        "relative rounded-lg border p-4",
        {
          "bg-background text-foreground": variant === "default",
          "border-blue-200 bg-blue-50 text-blue-900 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-200": variant === "info",
          "border-green-200 bg-green-50 text-green-900 dark:border-green-800 dark:bg-green-950 dark:text-green-200": variant === "success",
          "border-red-200 bg-red-50 text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-200": variant === "error",
          "border-yellow-200 bg-yellow-50 text-yellow-900 dark:border-yellow-800 dark:bg-yellow-950 dark:text-yellow-200": variant === "warning",
        },
        className
      )}
    >
      <div className="flex items-start gap-4">
        <Icon className="h-5 w-5" />
        <div className="flex-1">
          {title && (
            <h5 className="mb-1 font-medium leading-none tracking-tight">
              {title}
            </h5>
          )}
          <div className="text-sm">{children}</div>
        </div>
      </div>
    </div>
  )
} 