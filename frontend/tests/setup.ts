export {};

declare global {
  var WebSocket: typeof WebSocket;
  var performance: Performance;
  var console: Console;
}

// Mock browser environment
declare global {
  interface Window {
    WebSocket: typeof WebSocket;
    performance: Performance;
    console: Console;
  }
  var Response: typeof Response;
  var WebSocket: typeof WebSocket;
  var performance: Performance;
  var window: Window;
}

// Mock Response
class MockResponse {
  constructor(public body: any, public status: number = 200) {}
  json() {
    return Promise.resolve(this.body);
  }
  clone() {
    return new MockResponse(this.body, this.status);
  }
}

// Mock NextResponse
const NextResponse = {
  json: (body: any, status: number = 200) => new MockResponse(body, status),
  redirect: (url: string) => new MockResponse({ url }, 307),
  error: () => new MockResponse({ error: 'Internal Server Error' }, 500),
} as const;

// Mock WebSocket
class MockWebSocket implements Omit<WebSocket, keyof typeof WebSocket> {
  public readyState: number = 0; // CONNECTING
  public url: string;
  public protocol: string = '';
  public binaryType: BinaryType = 'blob';
  public bufferedAmount: number = 0;
  public extensions: string = '';
  public onopen: ((this: WebSocket, ev: Event) => any) | null = null;
  public onmessage: ((this: WebSocket, ev: MessageEvent) => any) | null = null;
  public onerror: ((this: WebSocket, ev: Event) => any) | null = null;
  public onclose: ((this: WebSocket, ev: CloseEvent) => any) | null = null;

  private eventListeners: { [key: string]: EventListenerOrEventListenerObject[] } = {};

  constructor(url: string) {
    this.url = url;
  }

  addEventListener<K extends keyof WebSocketEventMap>(
    type: K,
    listener: (this: WebSocket, ev: WebSocketEventMap[K]) => any,
    options?: boolean | AddEventListenerOptions
  ): void;
  addEventListener(
    type: string,
    listener: EventListenerOrEventListenerObject,
    options?: boolean | AddEventListenerOptions
  ): void {
    if (!this.eventListeners[type]) {
      this.eventListeners[type] = [];
    }
    this.eventListeners[type].push(listener);
  }

  removeEventListener<K extends keyof WebSocketEventMap>(
    type: K,
    listener: (this: WebSocket, ev: WebSocketEventMap[K]) => any,
    options?: boolean | EventListenerOptions
  ): void;
  removeEventListener(
    type: string,
    listener: EventListenerOrEventListenerObject,
    options?: boolean | EventListenerOptions
  ): void {
    if (!this.eventListeners[type]) return;
    this.eventListeners[type] = this.eventListeners[type].filter(l => l !== listener);
  }

  dispatchEvent(event: Event): boolean {
    const listeners = this.eventListeners[event.type] || [];
    listeners.forEach(listener => {
      if (typeof listener === 'function') {
        listener.call(this, event);
      } else {
        listener.handleEvent(event);
      }
    });
    return true;
  }

  send(data: string | ArrayBufferLike | Blob | ArrayBufferView) {
    // Mock implementation
  }

  close(code?: number, reason?: string) {
    this.readyState = 2; // CLOSING
    const closeEvent = new Event('close') as CloseEvent;
    Object.defineProperty(closeEvent, 'code', { value: code || 1000 });
    Object.defineProperty(closeEvent, 'reason', { value: reason || '' });
    this.dispatchEvent(closeEvent);
    this.readyState = 3; // CLOSED
  }

  // Helper methods for testing
  simulateOpen() {
    this.readyState = 1; // OPEN
    this.dispatchEvent(new Event('open'));
  }

  simulateError() {
    this.readyState = 3; // CLOSED
    this.dispatchEvent(new Event('error'));
  }

  simulateMessage(data: any) {
    const messageEvent = new MessageEvent('message', { data });
    this.dispatchEvent(messageEvent);
  }

  simulateClose(code?: number, reason?: string) {
    this.close(code, reason);
  }
}

// Mock global objects
const mockWebSocket = jest.fn((url: string) => new MockWebSocket(url)) as unknown as typeof WebSocket;
Object.defineProperties(mockWebSocket, {
  CONNECTING: { value: 0 },
  OPEN: { value: 1 },
  CLOSING: { value: 2 },
  CLOSED: { value: 3 },
});

// Create mock performance object
const mockPerformance = {
  now: () => Date.now(),
  getEntriesByType: () => [],
  mark: () => {},
  measure: () => {},
  clearMarks: () => {},
  clearMeasures: () => {},
  timeOrigin: Date.now(),
  toJSON: () => ({}),
  timing: {
    navigationStart: Date.now() - 1000,
    unloadEventStart: Date.now() - 900,
    unloadEventEnd: Date.now() - 800,
    redirectStart: 0,
    redirectEnd: 0,
    fetchStart: Date.now() - 700,
    domainLookupStart: Date.now() - 600,
    domainLookupEnd: Date.now() - 500,
    connectStart: Date.now() - 400,
    connectEnd: Date.now() - 300,
    secureConnectionStart: Date.now() - 350,
    requestStart: Date.now() - 200,
    requestEnd: Date.now() - 100,
    responseStart: Date.now() - 50,
    responseEnd: Date.now(),
    domLoading: Date.now(),
    domInteractive: Date.now() + 100,
    domContentLoadedEventStart: Date.now() + 200,
    domContentLoadedEventEnd: Date.now() + 300,
    domComplete: Date.now() + 400,
    loadEventStart: Date.now() + 500,
    loadEventEnd: Date.now() + 600,
  },
} as unknown as Performance;

// Create mock window object
const mockWindow = {
  WebSocket: mockWebSocket,
  performance: mockPerformance,
  console: {
    log: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
  },
  // Add required Window properties
  clientInformation: {} as Navigator,
  closed: false,
  customElements: {} as CustomElementRegistry,
  devicePixelRatio: 1,
  document: {} as Document,
  doNotTrack: null,
  external: {} as External,
  frameElement: null,
  frames: {} as Window,
  history: {} as History,
  innerHeight: 0,
  innerWidth: 0,
  length: 0,
  localStorage: {} as Storage,
  location: {} as Location,
  name: '',
  navigator: {} as Navigator,
  opener: null,
  outerHeight: 0,
  outerWidth: 0,
  pageXOffset: 0,
  pageYOffset: 0,
  parent: {} as Window,
  screen: {} as Screen,
  screenLeft: 0,
  screenTop: 0,
  screenX: 0,
  screenY: 0,
  scrollX: 0,
  scrollY: 0,
  self: {} as Window,
  sessionStorage: {} as Storage,
  status: '',
  styleMedia: {} as StyleMedia,
  toolbar: {} as BarProp,
  top: {} as Window,
  visualViewport: null,
} as unknown as Window;

// Define global objects
Object.defineProperties(global, {
  WebSocket: { value: mockWebSocket },
  Response: { value: MockResponse as unknown as typeof Response },
  NextResponse: { value: NextResponse },
  performance: { value: mockPerformance },
  window: { value: mockWindow },
});

// Mock axios
const mockAxiosInstance = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  interceptors: {
    request: { use: jest.fn(), eject: jest.fn() },
    response: { use: jest.fn(), eject: jest.fn() },
  },
};

const mockAxios = {
  create: jest.fn(() => mockAxiosInstance),
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  interceptors: {
    request: { use: jest.fn(), eject: jest.fn() },
    response: { use: jest.fn(), eject: jest.fn() },
  },
  defaults: {},
  getUri: jest.fn(),
  request: jest.fn(),
  head: jest.fn(),
  options: jest.fn(),
  patch: jest.fn(),
};

jest.mock('axios', () => mockAxios);

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
  }),
  usePathname: () => '',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock next/headers
jest.mock('next/headers', () => ({
  headers: () => new Headers(),
  cookies: () => ({
    get: jest.fn(),
    set: jest.fn(),
    delete: jest.fn(),
  }),
}));

// Mock next/server
jest.mock('next/server', () => ({
  NextResponse: global.NextResponse,
})); 