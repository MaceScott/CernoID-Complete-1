"use client"

import { useEffect, useState } from "react"
import { CameraGrid } from "@/components/features/CameraGrid"
import { Loading } from "@/components/ui/loading"
import { useAuth } from "@/components/providers/auth-provider"

interface DashboardStats {
  activeUsers: number
  activeCameras: number
  recentAlerts: number
  recognitionsToday: number
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // TODO: Fetch actual stats
    const fetchStats = async () => {
      try {
        // Mock data
        setStats({
          activeUsers: 24,
          activeCameras: 8,
          recentAlerts: 3,
          recognitionsToday: 156
        })
      } catch (error) {
        console.error('Failed to fetch stats:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchStats()
  }, [])

  if (isLoading) {
    return <Loading />
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Welcome back, {user?.name}</h1>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-4">
        {stats && Object.entries(stats).map(([key, value]) => (
          <div key={key} className="rounded-lg border bg-card p-4">
            <h3 className="text-sm font-medium text-muted-foreground">
              {key.replace(/([A-Z])/g, ' $1').trim()}
            </h3>
            <p className="mt-2 text-2xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      {/* Live Camera Grid */}
      <div>
        <h2 className="mb-4 text-xl font-semibold">Live Cameras</h2>
        <CameraGrid 
          cameras={[
            // TODO: Fetch actual camera data
            { id: "1", name: "Main Entrance", status: "active" },
            { id: "2", name: "Back Door", status: "active" },
          ]} 
          columns={2}
        />
      </div>
    </div>
  )
} 