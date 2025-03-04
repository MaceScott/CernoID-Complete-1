import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useQuery, useMutation } from '@tanstack/react-query'
import { DataTable } from '@/components/ui/data-table'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge, type BadgeProps } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  LineChart, 
  BarChart, 
  PieChart 
} from '@/components/ui/charts'
import type { ColumnDef, Row } from '@tanstack/react-table'

interface SecurityEvent {
  id: string
  timestamp: string
  type: string
  severity: 'low' | 'medium' | 'high'
  description: string
  locations: string[]
}

interface Permission {
  id: string
  role: string
  resource: string
  action: 'read' | 'write' | 'admin'
  location: string
}

interface Zone {
  id: string
  name: string
  level: number
  requiredAccess: string[]
  locations: string[]
}

const severityVariantMap = {
  low: 'default',
  medium: 'secondary',
  high: 'destructive'
} as const;

export function SecurityDashboard() {
  const columns: ColumnDef<SecurityEvent>[] = [
    {
      accessorKey: 'timestamp',
      header: 'Time',
    },
    {
      accessorKey: 'type',
      header: 'Type',
    },
    {
      accessorKey: 'severity',
      header: 'Severity',
      cell: ({ row }: { row: Row<SecurityEvent> }) => (
        <Badge variant={severityVariantMap[row.original.severity]}>
          {row.original.severity}
        </Badge>
      ),
    },
    {
      accessorKey: 'description',
      header: 'Description',
    },
    {
      accessorKey: 'locations',
      header: 'Locations',
      cell: ({ row }: { row: Row<SecurityEvent> }) => row.original.locations.join(', '),
    },
  ];

  // Fetch security events
  const { data: events } = useQuery<SecurityEvent[]>({
    queryKey: ['security-events'],
    queryFn: async () => {
      const res = await fetch('/api/security/events')
      return res.json()
    }
  })

  // Fetch permissions
  const { data: permissions } = useQuery<Permission[]>({
    queryKey: ['permissions'],
    queryFn: async () => {
      const res = await fetch('/api/security/permissions')
      return res.json()
    }
  })

  // Fetch zones
  const { data: zones } = useQuery<Zone[]>({
    queryKey: ['zones'],
    queryFn: async () => {
      const res = await fetch('/api/security/zones')
      return res.json()
    }
  })

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Security Dashboard</h1>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="events">Events</TabsTrigger>
          <TabsTrigger value="permissions">Permissions</TabsTrigger>
          <TabsTrigger value="zones">Zones</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Active Users</CardTitle>
              </CardHeader>
              <CardContent>
                <LineChart 
                  data={[/* Active users data */]}
                  xField="time"
                  yField="count"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Security Events</CardTitle>
              </CardHeader>
              <CardContent>
                <PieChart 
                  data={[/* Event type distribution */]}
                  angleField="value"
                  colorField="type"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Access Attempts</CardTitle>
              </CardHeader>
              <CardContent>
                <BarChart 
                  data={[/* Access attempts data */]}
                  xField="zone"
                  yField="count"
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="events">
          <Card>
            <CardHeader>
              <CardTitle>Security Events</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={columns}
                data={events || []}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="permissions">
          <Card>
            <CardHeader>
              <CardTitle>Access Permissions</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={[
                  {
                    accessorKey: 'role',
                    header: 'Role'
                  },
                  {
                    accessorKey: 'resource',
                    header: 'Resource'
                  },
                  {
                    accessorKey: 'action',
                    header: 'Action',
                    cell: ({ row }) => (
                      <Badge>
                        {row.original.action}
                      </Badge>
                    )
                  },
                  {
                    accessorKey: 'location',
                    header: 'Location'
                  }
                ]}
                data={permissions || []}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="zones">
          <Card>
            <CardHeader>
              <CardTitle>Security Zones</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={[
                  {
                    accessorKey: 'name',
                    header: 'Zone Name'
                  },
                  {
                    accessorKey: 'level',
                    header: 'Security Level'
                  },
                  {
                    accessorKey: 'requiredAccess',
                    header: 'Required Access',
                    cell: ({ row }) => (
                      <div className="flex gap-1">
                        {row.original.requiredAccess.map(access => (
                          <Badge key={access} variant="outline">
                            {access}
                          </Badge>
                        ))}
                      </div>
                    )
                  },
                  {
                    accessorKey: 'locations',
                    header: 'Locations',
                    cell: ({ row }) => (
                      <div className="flex gap-1">
                        {row.original.locations.map(location => (
                          <Badge key={location} variant="outline">
                            {location}
                          </Badge>
                        ))}
                      </div>
                    )
                  }
                ]}
                data={zones || []}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle>Active Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                {/* Example alerts */}
                <Alert className="mb-4">
                  <AlertTitle>Unauthorized Access Attempt</AlertTitle>
                  <AlertDescription>
                    Multiple failed access attempts at Main Entrance
                  </AlertDescription>
                </Alert>
                <Alert className="mb-4">
                  <AlertTitle>Camera Offline</AlertTitle>
                  <AlertDescription>
                    Security camera in Zone B is offline
                  </AlertDescription>
                </Alert>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
} 