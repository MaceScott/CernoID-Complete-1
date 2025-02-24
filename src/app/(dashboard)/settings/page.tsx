"use client"

import { useState } from "react"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/Button"
import { Alert } from "@/components/ui/alert"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Settings,
  Bell,
  Mail,
  Shield,
  Camera,
  Save,
  RefreshCw,
} from "lucide-react"

interface SettingsForm {
  notifications: {
    email: boolean
    push: boolean
    alerts: {
      motion: boolean
      face: boolean
      system: boolean
    }
  }
  email: string
  retentionDays: number
  cameraQuality: "low" | "medium" | "high"
}

export default function SettingsPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [settings, setSettings] = useState<SettingsForm>({
    notifications: {
      email: true,
      push: true,
      alerts: {
        motion: true,
        face: true,
        system: true,
      },
    },
    email: "admin@example.com",
    retentionDays: 30,
    cameraQuality: "high",
  })

  const handleSave = async () => {
    setIsLoading(true)
    setError(null)
    setSuccess(null)

    try {
      // TODO: Implement API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      setSuccess("Settings saved successfully")
    } catch (err) {
      setError("Failed to save settings")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">System Settings</h1>
        <Button
          onClick={handleSave}
          disabled={isLoading}
        >
          {isLoading ? (
            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Save Changes
        </Button>
      </div>

      {error && (
        <Alert variant="error">
          {error}
        </Alert>
      )}

      {success && (
        <Alert variant="success">
          {success}
        </Alert>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <h2 className="flex items-center text-lg font-semibold">
              <Bell className="mr-2 h-5 w-5" />
              Notification Settings
            </h2>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Alert Types</Label>
              <div className="space-y-2">
                {Object.entries(settings.notifications.alerts).map(([key, value]) => (
                  <div key={key} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={(e) => setSettings({
                        ...settings,
                        notifications: {
                          ...settings.notifications,
                          alerts: {
                            ...settings.notifications.alerts,
                            [key]: e.target.checked
                          }
                        }
                      })}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <span className="capitalize">{key} Alerts</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="flex items-center text-lg font-semibold">
              <Camera className="mr-2 h-5 w-5" />
              Camera Settings
            </h2>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Recording Quality</Label>
              <select
                value={settings.cameraQuality}
                onChange={(e) => setSettings({
                  ...settings,
                  cameraQuality: e.target.value as "low" | "medium" | "high"
                })}
                className="w-full rounded-md border border-input bg-background px-3 py-2"
              >
                <option value="low">Low (720p)</option>
                <option value="medium">Medium (1080p)</option>
                <option value="high">High (4K)</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label>Data Retention (days)</Label>
              <Input
                type="number"
                value={settings.retentionDays}
                onChange={(e) => setSettings({
                  ...settings,
                  retentionDays: parseInt(e.target.value)
                })}
                min={1}
                max={365}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 