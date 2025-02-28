const WebSocket = require('ws');
const http = require('http');

// Create an HTTP server
const server = http.createServer();

// Create a WebSocket server
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
    console.log('Client connected');

    ws.on('message', (message) => {
        console.log(`Received message: ${message}`);
        // Handle incoming messages from clients
        // For example, start/stop video streams
    });

    ws.on('close', () => {
        console.log('Client disconnected');
    });

    // Example: Send a message to the client
    ws.send(JSON.stringify({ message: 'Welcome to the WebSocket server!' }));
});

// Start the server on port 3001
server.listen(3001, () => {
    console.log('WebSocket server is running on ws://localhost:3001');
}); 