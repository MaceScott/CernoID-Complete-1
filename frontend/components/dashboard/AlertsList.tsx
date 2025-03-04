"use client"

import { useState } from "react"
import { useAlerts } from "@/lib/hooks"
import { Alert } from "@/types"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { AlertDetail } from "@/components/features/AlertDetail"
import {
  AlertTriangle,
  Bell,
  Camera,
  CheckCircle,
  Clock,
} from "lucide-react"
import { cn } from "@/lib/utils"

export default function AlertsList() {
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [typeFilter, setTypeFilter] = useState<string>("all")
  
  const { alerts, loading: isLoading, error, acknowledgeAlert, resolveAlert } = useAlerts()

  // Filter alerts based on selected filters
  const filteredAlerts = alerts.filter(alert => {
    if (statusFilter !== "all" && alert.status !== statusFilter) return false
    if (typeFilter !== "all" && alert.type !== typeFilter) return false
    return true
  })

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "motion":
        return <Camera className="h-4 w-4" />
      case "face":
        return <Bell className="h-4 w-4" />
      case "system":
      case "error":
        return <AlertTriangle className="h-4 w-4" />
      default:
        return <AlertTriangle className="h-4 w-4" />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
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

  const handleResolveAlert = async (id: string) => {
    try {
      await fetch(`/api/alerts/${id}/resolve`, {
        method: "POST",
      })
      setSelectedAlert(null)
    } catch (error) {
      console.error("Failed to resolve alert:", error)
    }
  }

  if (error) {
    return (
      <div className="text-center text-sm text-red-500 py-4">
        Failed to load alerts
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="text-center text-sm text-muted-foreground py-4">
        Loading alerts...
      </div>
    )
  }

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Recent Alerts</CardTitle>
          <div className="flex space-x-2">
            <Select
              value={statusFilter}
              onValueChange={setStatusFilter}
            >
              <SelectTrigger className="h-8 w-[120px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="new">New</SelectItem>
                <SelectItem value="read">Read</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={typeFilter}
              onValueChange={setTypeFilter}
            >
              <SelectTrigger className="h-8 w-[120px]">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="motion">Motion</SelectItem>
                <SelectItem value="face">Face</SelectItem>
                <SelectItem value="system">System</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredAlerts.length === 0 ? (
              <div className="text-center text-sm text-muted-foreground py-4">
                No alerts found
              </div>
            ) : (
              filteredAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className={cn(
                    "flex items-center justify-between p-4 rounded-lg cursor-pointer transition-colors",
                    "hover:bg-muted",
                    alert.status === "new" && "bg-muted/50"
                  )}
                  onClick={() => setSelectedAlert(alert)}
                >
                  <div className="flex items-center space-x-4">
                    <div className={cn(
                      "p-2 rounded-full",
                      getPriorityColor(alert.priority)
                    )}>
                      {getTypeIcon(alert.type)}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{alert.message}</p>
                      <div className="flex items-center space-x-2 mt-1">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">
                          {new Date(alert.timestamp).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {alert.status === "new" ? (
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                    ) : alert.status === "resolved" ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <Bell className="h-4 w-4 text-yellow-500" />
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <AlertDetail
        alert={selectedAlert}
        onClose={() => setSelectedAlert(null)}
        onResolve={handleResolveAlert}
      />
    </>
  )
} 