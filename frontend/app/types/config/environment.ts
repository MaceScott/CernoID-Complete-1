export interface EnvironmentConfig {
  environment: 'development' | 'production' | 'test';
  apiUrl: string;
  wsUrl: string;
  publicUrl: string;
  debug: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  retentionDays: number;
  timezone: string;
  locale: string;
  supportedLanguages: string[];
  defaultLanguage: string;
}

export const DEFAULT_ENV_CONFIG: EnvironmentConfig = {
  environment: 'development',
  apiUrl: 'http://localhost:3000/api',
  wsUrl: 'ws://localhost:3000/ws',
  publicUrl: 'http://localhost:3000',
  debug: true,
  logLevel: 'info',
  retentionDays: 30,
  timezone: 'UTC',
  locale: 'en-US',
  supportedLanguages: ['en', 'es', 'fr', 'de'],
  defaultLanguage: 'en',
}; 