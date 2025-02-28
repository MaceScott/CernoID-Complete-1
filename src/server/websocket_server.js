const WebSocket = require('ws');
const http = require('http');

const server = http.createServer();
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

server.listen(8080, () => {
    console.log('WebSocket server is listening on ws://localhost:8080');
}); 