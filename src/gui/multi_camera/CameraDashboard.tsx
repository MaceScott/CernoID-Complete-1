import React, { useState, useEffect } from 'react';

const CameraDashboard: React.FC = () => {
    const [cameraFeeds, setCameraFeeds] = useState<string[]>([]);
    const [videoSources, setVideoSources] = useState<{ [key: string]: string }>({});

    useEffect(() => {
        // Connect to WebSocket server to receive camera feeds
        const ws = new WebSocket('ws://localhost:8080');

        ws.onopen = () => {
            console.log('Connected to WebSocket server');
            // Request camera feeds
            ws.send(JSON.stringify({ action: 'getCameraFeeds' }));
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'cameraFeeds') {
                setCameraFeeds(data.feeds);
                setVideoSources(data.feeds.reduce((acc: any, feed: string) => {
                    acc[feed] = `http://localhost:8080/stream/${feed}`;
                    return acc;
                }, {}));
            }
        };

        ws.onclose = () => {
            console.log('Disconnected from WebSocket server');
        };

        return () => {
            ws.close();
        };
    }, []);

    return (
        <div className="camera-dashboard">
            <h1>Multi-Camera Monitoring Dashboard</h1>
            <div className="camera-feeds">
                {cameraFeeds.map((feed, index) => (
                    <div key={index} className="camera-feed">
                        <h2>{feed}</h2>
                        {/* Display video stream */}
                        <video src={videoSources[feed]} controls autoPlay muted />
                        {/* Placeholder for controls */}
                        <div className="controls">
                            <button>Start</button>
                            <button>Stop</button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default CameraDashboard; 