"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/components/providers/auth-provider"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import Alert from "@/components/ui/Alert"
import Loading from "@/components/ui/loading"
import { 
  Camera, 
  Users, 
  Bell, 
  Shield,
  CheckCircle,
  XCircle
} from "lucide-react"

// Quick status components
function StatusCard({ 
  title, 
  value, 
  icon: Icon, 
  status = "normal" 
}: { 
  title: string
  value: string | number
  icon: any
  status?: "normal" | "warning" | "error"
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center space-x-4">
          <div className={`rounded-full p-3 ${
            status === "normal" ? "bg-green-100 text-green-600" :
            status === "warning" ? "bg-yellow-100 text-yellow-600" :
            "bg-red-100 text-red-600"
          }`}>
            <Icon className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <h3 className="text-2xl font-bold">{value}</h3>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login')
    }
  }, [user, isLoading, router])

  if (isLoading) {
    return <Loading />
  }

  if (!user) {
    return null
  }

  // Mock data - replace with API calls
  const stats = {
    cameras: {
      total: 6,
      active: 4,
      status: "normal" as "normal"
    },
    users: {
      total: 12,
      active: 3,
      status: "normal" as "normal"
    },
    alerts: {
      total: 2,
      unread: 1,
      status: "warning" as "warning"
    },
    system: {
      status: "normal" as "normal",
      uptime: "5d 12h",
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Welcome back, {user.name}!</h1>
        <p className="text-muted-foreground">
          Here's what's happening in your security system
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatusCard
          title="Cameras"
          value={`${stats.cameras.active}/${stats.cameras.total}`}
          icon={Camera}
          status={stats.cameras.status}
        />
        <StatusCard
          title="Active Users"
          value={stats.users.active}
          icon={Users}
          status={stats.users.status}
        />
        <StatusCard
          title="Alerts"
          value={stats.alerts.unread}
          icon={Bell}
          status={stats.alerts.status}
        />
        <StatusCard
          title="System Status"
          value={stats.system.uptime}
          icon={Shield}
          status={stats.system.status}
        />
      </div>

      {/* System Status */}
      <Card>
        <CardHeader>
          <h2 className="text-xl font-bold">System Health</h2>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span>Authentication Service</span>
              </div>
              <span className="text-sm text-muted-foreground">Operational</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span>Camera Streams</span>
              </div>
              <span className="text-sm text-muted-foreground">Operational</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <XCircle className="h-5 w-5 text-red-500" />
                <span>Face Recognition</span>
              </div>
              <span className="text-sm text-red-500">Maintenance</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Alerts */}
      <Card>
        <CardHeader>
          <h2 className="text-xl font-bold">Recent Alerts</h2>
        </CardHeader>
        <CardContent>
          {stats.alerts.unread > 0 ? (
            <Alert variant="warning">
              You have {stats.alerts.unread} unread alert{stats.alerts.unread > 1 ? 's' : ''}
            </Alert>
          ) : (
            <p className="text-muted-foreground">No new alerts</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 