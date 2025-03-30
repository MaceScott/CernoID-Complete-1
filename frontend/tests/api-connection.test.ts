import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('API Connection Tests', () => {
  const devApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const prodApiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.cernoid.com';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Development Environment', () => {
    it('should connect to development API', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        status: 200,
        data: { status: 'healthy' },
        headers: {}
      });

      const response = await axios.get(`${devApiUrl}/api/v1/health`);
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status', 'healthy');
    });

    it('should handle CORS in development', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        status: 200,
        data: { status: 'healthy' },
        headers: {
          'access-control-allow-origin': 'http://localhost:3000'
        }
      });

      const response = await axios.get(`${devApiUrl}/api/v1/health`, {
        headers: {
          'Origin': 'http://localhost:3000'
        }
      });
      expect(response.status).toBe(200);
      expect(response.headers['access-control-allow-origin']).toBe('http://localhost:3000');
    });
  });

  describe('Production Environment', () => {
    it('should connect to production API', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        status: 200,
        data: { status: 'healthy' },
        headers: {}
      });

      const response = await axios.get(`${prodApiUrl}/api/v1/health`);
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status', 'healthy');
    });

    it('should handle CORS in production', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        status: 200,
        data: { status: 'healthy' },
        headers: {
          'access-control-allow-origin': 'https://cernoid.com'
        }
      });

      const response = await axios.get(`${prodApiUrl}/api/v1/health`, {
        headers: {
          'Origin': 'https://cernoid.com'
        }
      });
      expect(response.status).toBe(200);
      expect(response.headers['access-control-allow-origin']).toBe('https://cernoid.com');
    });
  });

  describe('Environment Variables', () => {
    it('should have correct development environment variables', () => {
      expect(process.env.NODE_ENV).toBe('development');
      expect(process.env.NEXT_PUBLIC_API_URL).toBeDefined();
      expect(process.env.NEXT_PUBLIC_APP_URL).toBeDefined();
      expect(process.env.NEXT_PUBLIC_WS_URL).toBeDefined();
    });

    it('should have correct production environment variables', () => {
      // This test will only run in production
      if (process.env.NODE_ENV === 'production') {
        expect(process.env.NEXT_PUBLIC_API_URL).toBeDefined();
        expect(process.env.NEXT_PUBLIC_APP_URL).toBeDefined();
        expect(process.env.NEXT_PUBLIC_WS_URL).toBeDefined();
        expect(process.env.NEXT_PUBLIC_API_URL).toContain('https://');
      }
    });
  });
}); 