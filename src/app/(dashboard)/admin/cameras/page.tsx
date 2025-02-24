"use client"

import { useState } from "react"
import { Camera } from "@/types"
import { DataTable } from "@/components/ui/data-table"
import { Button } from "@/components/ui/Button"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { Alert } from "@/components/ui/alert"
import { 
  CameraIcon,
  Settings,
  CheckCircle,
  XCircle,
  MapPin,
  MoreVertical,
  RefreshCw
} from "lucide-react"

// Mock data - replace with API call
const mockCameras: Camera[] = [
  {
    id: "1",
    name: "Front Door",
    location: "Main Entrance",
    status: "active",
    type: "outdoor",
    resolution: "1080p",
    lastActive: "2024-02-14T15:30:00Z"
  },
  {
    id: "2",
    name: "Reception",
    location: "Lobby",
    status: "active",
    type: "indoor",
    resolution: "4K",
    lastActive: "2024-02-14T15:29:00Z"
  },
  {
    id: "3",
    name: "Parking Lot",
    location: "Rear",
    status: "inactive",
    type: "outdoor",
    resolution: "1080p",
    lastActive: "2024-02-13T10:15:00Z"
  }
]

export default function CamerasPage() {
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRefresh = async () => {
    setIsLoading(true)
    setError(null)
    try {
      // TODO: Implement refresh logic with API
      await new Promise(resolve => setTimeout(resolve, 1000))
    } catch (err) {
      setError('Failed to refresh camera status')
    } finally {
      setIsLoading(false)
    }
  }

  const columns = [
    {
      key: "name",
      title: "Name",
      render: (camera: Camera) => (
        <div className="flex items-center">
          <CameraIcon className="mr-2 h-4 w-4 text-muted-foreground" />
          {camera.name}
        </div>
      )
    },
    {
      key: "location",
      title: "Location",
      render: (camera: Camera) => (
        <div className="flex items-center">
          <MapPin className="mr-2 h-4 w-4 text-muted-foreground" />
          {camera.location}
        </div>
      )
    },
    {
      key: "status",
      title: "Status",
      render: (camera: Camera) => (
        <div className="flex items-center">
          {camera.status === "active" ? (
            <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
          ) : (
            <XCircle className="mr-2 h-4 w-4 text-red-500" />
          )}
          {camera.status.charAt(0).toUpperCase() + camera.status.slice(1)}
        </div>
      )
    },
    { key: "type", title: "Type" },
    { key: "resolution", title: "Resolution" },
    {
      key: "lastActive",
      title: "Last Active",
      render: (camera: Camera) => (
        new Date(camera.lastActive).toLocaleString()
      )
    },
    {
      key: "actions",
      title: "",
      render: (camera: Camera) => (
        <Button variant="ghost" size="sm">
          <Settings className="h-4 w-4" />
        </Button>
      )
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Camera Management</h1>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh Status
          </Button>
          <Button>
            <CameraIcon className="mr-2 h-4 w-4" />
            Add Camera
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
            data={mockCameras}
            columns={columns}
            searchable
            onRowClick={setSelectedCamera}
          />
        </CardContent>
      </Card>
    </div>
  )
} 