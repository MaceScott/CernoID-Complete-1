"use client"

import { useState } from "react"
import { CameraGrid } from "@/components/features/CameraGrid"
import { Button } from "@/components/ui/Button"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import Alert from "@/components/ui/Alert"
import { 
  Grid2x2, 
  Grid3x3,
  LayoutGrid,
  RefreshCw
} from "lucide-react"
import { Camera } from "@/types"

// Mock data - replace with real API call
const mockCameras: Camera[] = [
  { id: "1", name: "Front Door", status: "active", location: "Entrance", type: "outdoor", resolution: "1080p", lastActive: new Date().toISOString() },
  { id: "2", name: "Back Door", status: "active", location: "Backyard", type: "outdoor", resolution: "720p", lastActive: new Date().toISOString() },
  { id: "3", name: "Parking Lot", status: "inactive", location: "Parking Area", type: "outdoor", resolution: "1080p", lastActive: new Date().toISOString() },
  { id: "4", name: "Reception", status: "active", location: "Lobby", type: "indoor", resolution: "1080p", lastActive: new Date().toISOString() },
];

export default function ReviewPage() {
  const [columns, setColumns] = useState<2 | 3 | 4>(2)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRefresh = async () => {
    setIsLoading(true)
    setError(null)
    try {
      // TODO: Implement real refresh logic
      await new Promise(resolve => setTimeout(resolve, 1000))
    } catch (err) {
      setError('Failed to refresh cameras')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">Camera Review</h2>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setColumns(2)}
                className={columns === 2 ? "bg-primary text-primary-foreground" : ""}
              >
                <Grid2x2 className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setColumns(3)}
                className={columns === 3 ? "bg-primary text-primary-foreground" : ""}
              >
                <Grid3x3 className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setColumns(4)}
                className={columns === 4 ? "bg-primary text-primary-foreground" : ""}
              >
                <LayoutGrid className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="error" className="mb-4">
              {error}
            </Alert>
          )}
          <CameraGrid
            initialCameras={mockCameras}
            columns={columns}
          />
        </CardContent>
      </Card>
    </div>
  )
} 