import winston from 'winston'
import { ElasticsearchTransport } from 'winston-elasticsearch'

const logLevels = {
  error: 0,
  warn: 1,
  info: 2,
  debug: 3,
}

export const logger = winston.createLogger({
  levels: logLevels,
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'surveillance-system' },
  transports: [
    // Console logging
    new winston.transports.Console({
      level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
    }),
    // File logging
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    }),
    // Elasticsearch logging
    new ElasticsearchTransport({
      level: 'info',
      clientOpts: {
        node: process.env.ELASTICSEARCH_URL,
        auth: {
          username: process.env.ELASTICSEARCH_USERNAME,
          password: process.env.ELASTICSEARCH_PASSWORD,
        },
      },
      indexPrefix: 'surveillance-logs',
    })
  ]
}) 