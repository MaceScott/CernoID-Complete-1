"use client"

import { useRef, useEffect, useState } from "react"
import { Face } from "@/types"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import {
  Alert,
  AlertDescription,
} from "@/components/ui/alert"
import {
  ZoomIn,
  ZoomOut,
  Save,
  RefreshCw,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface RecognitionViewerProps {
  imageUrl: string
  faces: Face[]
  loading?: boolean
  error?: string
  onRefresh?: () => void
}

export function RecognitionViewer({
  imageUrl,
  faces,
  loading,
  error,
  onRefresh,
}: RecognitionViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [zoom, setZoom] = useState(1)
  const [showLandmarks, setShowLandmarks] = useState(true)
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.5)
  const [selectedFace, setSelectedFace] = useState<Face | null>(null)

  useEffect(() => {
    if (!imageUrl || !canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const image = new Image()
    image.src = imageUrl
    image.onload = () => {
      // Reset canvas and apply zoom
      canvas.width = image.width * zoom
      canvas.height = image.height * zoom
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.scale(zoom, zoom)
      ctx.drawImage(image, 0, 0)

      // Draw faces that meet confidence threshold
      faces.forEach((face, index) => {
        if (face.confidence >= confidenceThreshold) {
          const isSelected = selectedFace !== null && index === faces.indexOf(selectedFace)
          drawFace(ctx, face, isSelected)
        }
      })
    }
  }, [imageUrl, faces, zoom, showLandmarks, confidenceThreshold, selectedFace])

  const drawFace = (
    ctx: CanvasRenderingContext2D,
    face: Face,
    isSelected: boolean
  ) => {
    const [x1, y1, x2, y2] = face.bbox

    // Draw bounding box
    ctx.strokeStyle = isSelected ? 
      "hsl(var(--secondary))" : 
      "hsl(var(--primary))"
    ctx.lineWidth = 2
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)

    // Draw confidence score
    ctx.fillStyle = "hsl(var(--background))"
    ctx.fillRect(x1, y1 - 20, 70, 20)
    ctx.fillStyle = "hsl(var(--foreground))"
    ctx.font = "12px var(--font-sans)"
    ctx.fillText(
      `${(face.confidence * 100).toFixed(1)}%`,
      x1 + 5,
      y1 - 5
    )

    // Draw facial landmarks if enabled
    if (showLandmarks && face.landmarks) {
      ctx.fillStyle = "hsl(var(--secondary))"
      face.landmarks.forEach(([x, y]: number[]) => {
        ctx.beginPath()
        ctx.arc(x, y, 2, 0, 2 * Math.PI)
        ctx.fill()
      })
    }
  }

  const handleSaveImage = () => {
    if (!canvasRef.current) return
    
    const link = document.createElement("a")
    link.download = "recognition-results.png"
    link.href = canvasRef.current.toDataURL()
    link.click()
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription className="flex items-center justify-between">
          {error}
          {onRefresh && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onRefresh}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          )}
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="grid gap-6 md:grid-cols-3">
      <Card className="md:col-span-2">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-base font-medium">
            Recognition Results
          </CardTitle>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setZoom(z => Math.max(0.5, z - 0.1))}
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setZoom(z => Math.min(2, z + 0.1))}
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleSaveImage}
            >
              <Save className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex h-[400px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : (
            <div className="flex justify-center overflow-auto">
              <canvas
                ref={canvasRef}
                className="max-w-full h-auto cursor-pointer"
                onClick={(e) => {
                  const rect = canvasRef.current?.getBoundingClientRect()
                  if (!rect) return
                  
                  const x = (e.clientX - rect.left) / zoom
                  const y = (e.clientY - rect.top) / zoom
                  
                  const clickedFace = faces.find(face => {
                    const [x1, y1, x2, y2] = face.bbox
                    return x >= x1 && x <= x2 && y >= y1 && y <= y2
                  })
                  
                  setSelectedFace(clickedFace || null)
                }}
              />
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label>Confidence Threshold</Label>
            <Slider
              value={[confidenceThreshold]}
              onValueChange={(values: number[]) => setConfidenceThreshold(values[0])}
              min={0}
              max={1}
              step={0.05}
              className="w-full"
            />
            <div className="text-right text-sm text-muted-foreground">
              {(confidenceThreshold * 100).toFixed(0)}%
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="landmarks"
              checked={showLandmarks}
              onCheckedChange={setShowLandmarks}
            />
            <Label htmlFor="landmarks">Show Facial Landmarks</Label>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 