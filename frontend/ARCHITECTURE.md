# CernoID System Architecture

## Overview

CernoID is a comprehensive security and access control system that combines facial recognition, traditional authentication, and physical access management. The system is built using Next.js 13+ with the App Router pattern and follows modern web development best practices.

## Core Components

### Authentication System
- **LoginForm Component** (`app/components/Auth/LoginForm.tsx`)
  - Handles both traditional and face recognition login
  - Uses face-api.js for client-side face detection
  - Provides real-time feedback during authentication
  - Manages form state and validation

- **AuthProvider** (`app/providers/AuthProvider.tsx`)
  - Global authentication state management
  - Session handling and persistence
  - Protected route management
  - User context distribution

### API Routes

#### Authentication Endpoints
- **Traditional Login** (`app/api/auth/login/route.ts`)
  - Email/password validation
  - JWT token generation
  - Session cookie management

- **Face Login** (`app/api/auth/login/face/route.ts`)
  - Face image data processing
  - Simulated face recognition (placeholder for production implementation)
  - Secure session management

### Middleware
- **Route Protection** (`middleware.ts`)
  - JWT validation
  - Public route allowlist
  - User context propagation
  - Static asset handling

### Database Schema
The system uses PostgreSQL with Prisma ORM, defining several key models:

- **User**: Core user management and authentication
- **Account**: OAuth provider integration
- **Session**: Authentication state management
- **Permission**: Role-based access control
- **Camera**: Security camera management
- **Recognition**: Face recognition event tracking
- **Zone**: Physical security zone definition
- **AccessPoint**: Access control point management
- **Alert**: Security incident tracking

## Data Flow

1. **Authentication Flow**
   ```
   User -> LoginForm -> API Routes -> Database
                    -> face-api.js -> Face Login API -> Database
   ```

2. **Session Management**
   ```
   Request -> Middleware -> JWT Validation -> Protected Route/API
                       -> Invalid -> Login Redirect
   ```

3. **Access Control**
   ```
   User -> AccessPoint -> Zone Check -> Permission Validation -> Access Grant/Deny
   ```

## Security Features

1. **Authentication**
   - JWT-based session management
   - Secure HTTP-only cookies
   - Face recognition capabilities
   - Password hashing and validation

2. **Authorization**
   - Role-based access control (RBAC)
   - Resource-level permissions
   - Zone-based access restrictions

3. **API Security**
   - Request validation using Zod
   - CORS protection
   - Rate limiting (TODO)
   - Input sanitization

## Development Practices

1. **Type Safety**
   - Strict TypeScript configuration
   - Zod schema validation
   - Prisma-generated types

2. **Code Organization**
   - Next.js 13+ App Router conventions
   - Component-based architecture
   - Centralized state management
   - Consistent file structure

3. **Error Handling**
   - Structured error responses
   - Validation error formatting
   - Proper error logging
   - User-friendly error messages

## Environment Configuration

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: Secret key for JWT signing
- `NEXT_PUBLIC_APP_URL`: Application URL for CORS

## Future Improvements

1. **Authentication**
   - Implement proper face recognition service
   - Add multi-factor authentication
   - Enhanced session management

2. **Security**
   - Add rate limiting
   - Implement audit logging
   - Enhanced error tracking

3. **Performance**
   - Add caching layer
   - Optimize face detection
   - Implement real-time updates

## Deployment

The system is containerized using Docker and can be deployed using:
```bash
docker compose up -d
```

Environment-specific configurations are managed through Docker Compose and environment files. 