"use client"

import { useState } from "react"
import { Alert as AlertType } from "@/types"
import DataTable from "@/components/ui/data-table"
import { Button } from "@/components/ui/Button"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import Alert from "@/components/ui/Alert"
import { 
  Bell,
  AlertTriangle,
  Camera,
  CheckCircle,
  Clock,
  Filter,
  RefreshCw
} from "lucide-react"

// Mock data - replace with API call
const mockAlerts: AlertType[] = [
  {
    id: "1",
    type: "motion",
    message: "Motion detected in restricted area",
    timestamp: new Date().toISOString(),
    status: "new",
    priority: "high",
    cameraId: "cam-1"
  },
  {
    id: "2",
    type: "face",
    message: "Unknown person detected",
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    status: "read",
    priority: "medium",
    cameraId: "cam-2"
  },
  {
    id: "3",
    type: "system",
    message: "Camera offline for more than 5 minutes",
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    status: "resolved",
    priority: "low",
    cameraId: "cam-3"
  }
]

export default function AlertsPage() {
  const [selectedAlert, setSelectedAlert] = useState<AlertType | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRefresh = async () => {
    setIsLoading(true)
    setError(null)
    try {
      // TODO: Implement refresh logic with API
      await new Promise(resolve => setTimeout(resolve, 1000))
    } catch (err) {
      setError('Failed to refresh alerts')
    } finally {
      setIsLoading(false)
    }
  }

  const getPriorityColor = (priority: AlertType["priority"]) => {
    switch (priority) {
      case "high":
        return "text-red-500"
      case "medium":
        return "text-yellow-500"
      case "low":
        return "text-blue-500"
      default:
        return "text-gray-500"
    }
  }

  const getStatusIcon = (status: AlertType["status"]) => {
    switch (status) {
      case "new":
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case "read":
        return <CheckCircle className="h-4 w-4 text-yellow-500" />
      case "resolved":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      default:
        return null
    }
  }

  const columns = [
    {
      key: "status",
      title: "Status",
      render: (alert: AlertType) => (
        <div className="flex items-center">
          {getStatusIcon(alert.status)}
          <span className="ml-2 capitalize">{alert.status}</span>
        </div>
      )
    },
    {
      key: "type",
      title: "Type",
      render: (alert: AlertType) => (
        <div className="flex items-center">
          {alert.type === "motion" && <Camera className="mr-2 h-4 w-4" />}
          {alert.type === "face" && <Bell className="mr-2 h-4 w-4" />}
          {alert.type === "system" && <AlertTriangle className="mr-2 h-4 w-4" />}
          <span className="capitalize">{alert.type}</span>
        </div>
      )
    },
    {
      key: "message",
      title: "Message"
    },
    {
      key: "priority",
      title: "Priority",
      render: (alert: AlertType) => (
        <span className={`font-medium ${getPriorityColor(alert.priority)}`}>
          {alert.priority.toUpperCase()}
        </span>
      )
    },
    {
      key: "timestamp",
      title: "Time",
      render: (alert: AlertType) => (
        <div className="flex items-center">
          <Clock className="mr-2 h-4 w-4 text-muted-foreground" />
          {new Date(alert.timestamp).toLocaleString()}
        </div>
      )
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Security Alerts</h1>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button variant="outline">
            <Filter className="mr-2 h-4 w-4" />
            Filter
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="error">
          {error}
        </Alert>
      )}

      <Card>
        <CardContent className="p-6">
          <DataTable
            data={mockAlerts}
            columns={columns}
            searchable
            onRowClick={setSelectedAlert}
          />
        </CardContent>
      </Card>
    </div>
  )
} 