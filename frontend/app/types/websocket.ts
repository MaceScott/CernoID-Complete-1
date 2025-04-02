export interface WebSocketMessage {
  type: string;
  payload: {
    data: any;
  };
}

export interface WebSocketHandler {
  (data: any): void;
} 