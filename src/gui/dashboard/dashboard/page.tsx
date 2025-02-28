import { CameraFeed } from "@/components/features/CameraFeed"

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <CameraFeed 
          id="camera1"
          name="Main Entrance"
          status="active"
        />
        <CameraFeed 
          id="camera2"
          name="Back Door"
          status="active"
        />
        <CameraFeed 
          id="camera3"
          name="Parking Lot"
          status="inactive"
        />
      </div>
    </div>
  )
} 