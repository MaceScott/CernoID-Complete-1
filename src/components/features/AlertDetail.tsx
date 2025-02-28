"use client"

import { Alert as AlertType } from "@/types"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/Dialog"
import { Button } from "@/components/ui/Button"
import Alert from "@/components/ui/Alert"
import {
  Camera,
  Bell,
  AlertTriangle,
  Clock,
  CheckCircle,
  XCircle,
  MoreVertical,
} from "lucide-react"

interface AlertDetailProps {
  alert: AlertType | null
  onClose: () => void
  onResolve: (id: string) => Promise<void>
}

export function AlertDetail({ alert, onClose, onResolve }: AlertDetailProps) {
  if (!alert) return null

  const getTypeIcon = () => {
    switch (alert.type) {
      case "motion":
        return <Camera className="h-5 w-5" />
      case "face":
        return <Bell className="h-5 w-5" />
      case "system":
        return <AlertTriangle className="h-5 w-5" />
      default:
        return <AlertTriangle className="h-5 w-5" />
    }
  }

  const getPriorityColor = () => {
    switch (alert.priority) {
      case "high":
        return "bg-red-100 text-red-700"
      case "medium":
        return "bg-yellow-100 text-yellow-700"
      case "low":
        return "bg-blue-100 text-blue-700"
      default:
        return "bg-gray-100 text-gray-700"
    }
  }

  return (
    <Dialog open={!!alert} onOpenChange={() => onClose()}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            {getTypeIcon()}
            <span>Alert Details</span>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-muted-foreground">Status:</span>
              <span className="flex items-center">
                {alert.status === "new" ? (
                  <AlertTriangle className="mr-1 h-4 w-4 text-red-500" />
                ) : alert.status === "resolved" ? (
                  <CheckCircle className="mr-1 h-4 w-4 text-green-500" />
                ) : (
                  <Bell className="mr-1 h-4 w-4 text-yellow-500" />
                )}
                {alert.status.charAt(0).toUpperCase() + alert.status.slice(1)}
              </span>
            </div>
            <span className={`rounded-full px-2 py-1 text-xs font-medium ${getPriorityColor()}`}>
              {alert.priority.toUpperCase()}
            </span>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Message:</p>
            <p className="text-sm">{alert.message}</p>
          </div>

          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              {new Date(alert.timestamp).toLocaleString()}
            </span>
          </div>

          {alert.cameraId && (
            <div className="flex items-center space-x-2">
              <Camera className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Camera ID: {alert.cameraId}
              </span>
            </div>
          )}
        </div>

        <DialogFooter className="flex justify-between">
          <Button
            variant="outline"
            onClick={onClose}
          >
            Close
          </Button>
          {alert.status !== "resolved" && (
            <Button
              onClick={() => onResolve(alert.id)}
              className="bg-green-600 hover:bg-green-700"
            >
              <CheckCircle className="mr-2 h-4 w-4" />
              Mark as Resolved
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 