"use client"

import { useState, useEffect } from "react"
import { Camera } from "@/types"
import { useWebSocketMessage } from "@/lib/websocket"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { Alert } from "@/components/ui/alert"
import { Camera as CameraIcon, AlertTriangle, Wifi, WifiOff } from "lucide-react"

interface CameraGridProps {
  initialCameras: Camera[]
  columns: 2 | 3 | 4
}

export function CameraGrid({ initialCameras, columns }: CameraGridProps) {
  const [cameras, setCameras] = useState(initialCameras)
  const statusUpdate = useWebSocketMessage<{ id: string; status: string }>('camera_status')

  useEffect(() => {
    if (statusUpdate) {
      setCameras(prev => prev.map(camera => 
        camera.id === statusUpdate.id 
          ? { ...camera, status: statusUpdate.status }
          : camera
      ))
    }
  }, [statusUpdate])

  const [streams, setStreams] = useState<Record<string, boolean>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    // Simulate stream connections
    const newStreams: Record<string, boolean> = {}
    cameras.forEach(camera => {
      newStreams[camera.id] = camera.status === "active"
    })
    setStreams(newStreams)
  }, [cameras])

  const handleStreamError = (cameraId: string) => {
    setErrors(prev => ({
      ...prev,
      [cameraId]: "Stream connection failed"
    }))
  }

  return (
    <div
      className="grid gap-4"
      style={{
        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`
      }}
    >
      {cameras.map((camera) => (
        <Card key={camera.id} className="overflow-hidden">
          <CardHeader className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CameraIcon className="h-4 w-4" />
                <h3 className="font-medium">{camera.name}</h3>
              </div>
              {camera.status === "active" ? (
                <Wifi className="h-4 w-4 text-green-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-red-500" />
              )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="aspect-video bg-gray-900">
              {camera.status === "active" ? (
                streams[camera.id] ? (
                  <div className="flex h-full items-center justify-center">
                    {/* Replace with actual video stream component */}
                    <div className="text-sm text-gray-400">
                      Live Stream
                    </div>
                  </div>
                ) : (
                  <div className="flex h-full items-center justify-center">
                    <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-600 border-t-transparent" />
                  </div>
                )
              ) : (
                <div className="flex h-full items-center justify-center text-gray-600">
                  <AlertTriangle className="h-6 w-6" />
                  <span className="ml-2">Camera Offline</span>
                </div>
              )}
            </div>
            {errors[camera.id] && (
              <Alert variant="error" className="m-2">
                {errors[camera.id]}
              </Alert>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
} 