import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DataTable } from '@/components/ui/data-table';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useAuth } from '@/hooks/useAuth';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useState, useEffect } from 'react';

interface SecurityEvent {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high';
  timestamp: string;
  description: string;
  status: 'open' | 'investigating' | 'resolved';
}

interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkLoad: number;
}

export function SecurityDashboard() {
  const { user } = useAuth();
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpuUsage: 0,
    memoryUsage: 0,
    diskUsage: 0,
    networkLoad: 0,
  });

  // Subscribe to security events
  useWebSocket({
    url: '/api/security/events',
    onMessage: (data) => {
      if (data.type === 'security_event') {
        setEvents(prev => [data.event, ...prev]);
      } else if (data.type === 'system_metrics') {
        setMetrics(data.metrics);
      }
    },
  });

  const handleEventAction = async (eventId: string, action: string) => {
    try {
      const response = await fetch(`/api/security/events/${eventId}/${action}`, {
        method: 'POST',
      });
      if (response.ok) {
        setEvents(prev =>
          prev.map(event =>
            event.id === eventId
              ? { ...event, status: action === 'resolve' ? 'resolved' : 'investigating' }
              : event
          )
        );
      }
    } catch (error) {
      console.error('Failed to update event:', error);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Security Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="events">
            <TabsList>
              <TabsTrigger value="events">Events</TabsTrigger>
              <TabsTrigger value="metrics">System Metrics</TabsTrigger>
            </TabsList>
            <TabsContent value="events">
              <ScrollArea className="h-[400px]">
                <div className="space-y-4">
                  {events.map(event => (
                    <Alert key={event.id} className="relative">
                      <Badge
                        variant={
                          event.severity === 'high'
                            ? 'destructive'
                            : event.severity === 'medium'
                            ? 'warning'
                            : 'secondary'
                        }
                        className="absolute top-2 right-2"
                      >
                        {event.severity}
                      </Badge>
                      <AlertTitle>{event.type}</AlertTitle>
                      <AlertDescription>
                        <div className="mt-2 space-y-2">
                          <p>{event.description}</p>
                          <p className="text-sm text-muted-foreground">
                            {new Date(event.timestamp).toLocaleString()}
                          </p>
                          {event.status !== 'resolved' && (
                            <div className="space-x-2">
                              {event.status === 'open' && (
                                <Button
                                  size="sm"
                                  onClick={() => handleEventAction(event.id, 'investigate')}
                                >
                                  Investigate
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleEventAction(event.id, 'resolve')}
                              >
                                Resolve
                              </Button>
                            </div>
                          )}
                        </div>
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>
            <TabsContent value="metrics">
              <div className="grid gap-4 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>CPU Usage</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{metrics.cpuUsage}%</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Memory Usage</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{metrics.memoryUsage}%</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Disk Usage</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{metrics.diskUsage}%</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Network Load</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{metrics.networkLoad} Mbps</div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
} 