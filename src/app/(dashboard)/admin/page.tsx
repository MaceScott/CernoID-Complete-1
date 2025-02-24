"use client"

import { useState, useEffect } from "react"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/Button"
import { 
  Users, 
  Camera, 
  AlertTriangle, 
  Activity,
  Server,
  Clock,
  ArrowUp,
  ArrowDown,
  RefreshCw
} from "lucide-react"

interface SystemStatus {
  cpu: number
  memory: number
  storage: number
  uptime: string
  activeUsers: number
  activeCameras: number
  alerts: number
}

interface Event {
  id: string
  type: "recognition" | "alert" | "system"
  description: string
  timestamp: string
  status: "success" | "warning" | "error"
}

export default function AdminPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [events, setEvents] = useState<Event[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    setIsLoading(true)
    setError(null)
    try {
      // TODO: Replace with actual API calls
      await new Promise(resolve => setTimeout(resolve, 1000))
      setStatus({
        cpu: 45,
        memory: 60,
        storage: 75,
        uptime: "5 days, 12 hours",
        activeUsers: 3,
        activeCameras: 4,
        alerts: 1
      })
      setEvents([
        {
          id: "1",
          type: "recognition",
          description: "New face recognized: John Doe",
          timestamp: new Date().toISOString(),
          status: "success"
        },
        {
          id: "2",
          type: "alert",
          description: "Motion detected in restricted area",
          timestamp: new Date().toISOString(),
          status: "warning"
        }
      ])
    } catch (err) {
      setError("Failed to fetch system status")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (error) {
    return (
      <Alert variant="error">
        {error}
        <Button
          variant="outline"
          size="sm"
          onClick={fetchData}
          className="mt-2"
        >
          Retry
        </Button>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">System Overview</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchData}
          disabled={isLoading}
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-4">
              <Server className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-sm font-medium">CPU Usage</p>
                <p className="text-2xl font-bold">{status?.cpu}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
        {/* Add more status cards here */}
      </div>

      {/* Recent Events */}
      <Card>
        <CardHeader>
          <h2 className="text-xl font-bold">Recent Events</h2>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {events.map(event => (
              <div key={event.id} className="flex items-start space-x-4">
                <div className={`rounded-full p-2 ${
                  event.status === "success" ? "bg-green-100" :
                  event.status === "warning" ? "bg-yellow-100" :
                  "bg-red-100"
                }`}>
                  {event.type === "recognition" && <Users className="h-4 w-4" />}
                  {event.type === "alert" && <AlertTriangle className="h-4 w-4" />}
                  {event.type === "system" && <Server className="h-4 w-4" />}
                </div>
                <div>
                  <p className="font-medium">{event.description}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(event.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 