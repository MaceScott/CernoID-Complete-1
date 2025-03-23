"use client";

import React, { useState, useEffect, useRef } from "react";
import { Camera, AlertCircle, Maximize2, Square } from "lucide-react";
import { cn } from "@/lib/utils";
import { useWebSocketContext } from "@/providers/WebSocketProvider";
import { LoadingOverlay } from "@/components/shared/feedback";
import { Skeleton } from "@/components/ui/skeleton";
import { CameraConfig } from "@/types";
import { Box, CircularProgress, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';

interface CameraFeedProps {
  camera: CameraConfig;
  status: CameraConfig['status'];
  className?: string;
  onFullscreen?: () => void;
}

interface Recognition {
  name: string;
  confidence: number;
  box: { x: number; y: number; width: number; height: number };
}

export function CameraFeed({
  camera,
  status,
  className,
  onFullscreen,
}: CameraFeedProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [recognitions, setRecognitions] = useState<Recognition[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnecting, setIsConnecting] = useState(true);

  const { state, send } = useWebSocketContext();

  useEffect(() => {
    if (state.connected) {
      // Subscribe to camera feed
      send({ 
        type: 'subscribe', 
        payload: { 
          event: 'camera_feed',
          cameraId: camera.id 
        } 
      });
    }
  }, [state.connected, camera.id, send]);

  useEffect(() => {
    if (!videoRef.current) return;

    const video = videoRef.current;
    let stream: MediaStream | null = null;

    const setupVideo = async () => {
      try {
        setIsConnecting(true);
        if (camera.type === 'webcam') {
          stream = await navigator.mediaDevices.getUserMedia({ video: true });
          video.srcObject = stream;
        } else if (camera.type === 'ip' && camera.streamUrl) {
          video.src = camera.streamUrl;
        } else {
          setError("Camera stream URL is not configured");
          setIsLoading(false);
          setIsConnecting(false);
        }

        video.onloadedmetadata = () => {
          setIsLoading(false);
          setIsConnecting(false);
        };

        video.onerror = () => {
          setError("Failed to load video stream");
          setIsLoading(false);
          setIsConnecting(false);
        };
      } catch (err) {
        setError("Failed to connect to camera feed");
        setIsLoading(false);
        setIsConnecting(false);
        console.error(err);
      }
    };

    setupVideo();

    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [camera]);

  // Handle recognition updates
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'recognition' && data.payload.cameraId === camera.id) {
          setRecognitions(data.payload.recognitions);
        }
      } catch (error) {
        console.error('Failed to parse recognition data:', error);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [camera.id]);

  // Handle fullscreen toggle
  const toggleFullscreen = () => {
    const element = videoRef.current;
    if (!document.fullscreenElement) {
      element?.requestFullscreen().catch((err) => console.error("Fullscreen error:", err));
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch((err) => console.error("Exit fullscreen error:", err));
      setIsFullscreen(false);
    }
    onFullscreen?.();
  };

  if (isLoading) {
    return (
      <div className={cn("relative overflow-hidden rounded-lg bg-gray-900", className)}>
        <div className="aspect-video">
          <Skeleton className="h-full w-full" />
        </div>
        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between bg-gradient-to-t from-black/80 to-transparent p-4">
          <div>
            <Skeleton className="h-4 w-24" />
            <Skeleton className="mt-1 h-3 w-16" />
          </div>
          <Skeleton className="h-8 w-8 rounded-lg" />
        </div>
      </div>
    );
  }

  return (
    <div className={cn("relative overflow-hidden rounded-lg bg-gray-900", className)}>
      {/* Camera Feed */}
      <div className="relative aspect-video">
        <video ref={videoRef} autoPlay playsInline muted className="h-full w-full object-cover" />
        <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />

        {isConnecting && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900/90">
            <LoadingOverlay open={true} message="Loading camera feed..." />
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900/90">
            <div className="text-center text-white">
              <AlertCircle className="mx-auto h-8 w-8 text-red-500" />
              <p className="mt-2">{error}</p>
            </div>
          </div>
        )}

        {status === "inactive" && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900/90">
            <div className="text-center text-white">
              <Camera className="mx-auto h-8 w-8" />
              <p className="mt-2">Camera Offline</p>
            </div>
          </div>
        )}

        {!state.connected && !error && status === "active" && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900/90">
            <div className="text-center text-white">
              <LoadingOverlay open={true} message="Reconnecting..." />
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between bg-gradient-to-t from-black/80 to-transparent p-4">
        <div>
          <h3 className="text-sm font-medium text-white">{camera.name}</h3>
          <p className={cn("text-xs", status === "active" ? "text-green-400" : "text-red-400")}>
            {status === "active" ? "Active" : "Inactive"}
          </p>
        </div>
        <button
          onClick={toggleFullscreen}
          className="rounded-lg bg-white/10 p-2 text-white hover:bg-white/20"
          disabled={!state.connected || !!error}
        >
          {isFullscreen ? <Square className="h-5 w-5" /> : <Maximize2 className="h-5 w-5" />}
        </button>
      </div>
    </div>
  );
}
