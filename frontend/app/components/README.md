# Component Structure

## Directory Organization

```
components/
├── ui/                    # Reusable UI components (buttons, inputs, etc.)
├── shared/               # Shared components used across features
├── features/             # Feature-specific components
│   ├── dashboard/       # Dashboard-related components
│   ├── profile/         # Profile management components
│   ├── settings/        # Settings-related components
│   ├── recognition/     # Face recognition components
│   ├── cameras/         # Camera management components
│   └── admin/          # Admin panel components
├── Auth/                # Authentication-related components
├── Layout/              # Layout components (DashboardLayout, etc.)
├── Navigation/          # Navigation components (TopBar, Sidebar, etc.)
└── ErrorBoundary/       # Error boundary components
```

## Component Categories

### UI Components
Basic UI elements that follow our design system:
- Button
- Input
- Card
- Alert
- Modal
- etc.

### Shared Components
Reusable components used across multiple features:
- LoadingSpinner
- ErrorAlert
- ConfirmDialog
- NotificationBadge

### Feature Components
Components specific to feature modules:
- Dashboard: Analytics, Stats, etc.
- Profile: ProfileForm, SecuritySettings
- Settings: SystemSettings, Preferences
- Recognition: FaceDetection, RecognitionViewer
- Cameras: CameraGrid, CameraFeed
- Admin: UserManagement, SecurityDashboard

### Auth Components
Authentication-related components:
- LoginForm
- RegisterForm
- ForgotPasswordForm
- AuthGuard
- AdminGuard

### Layout Components
Page layout components:
- DashboardLayout
- AuthLayout
- AdminLayout

### Navigation Components
Navigation-related components:
- TopBar
- Sidebar
- Breadcrumbs

### Error Handling
Error boundary components:
- ErrorBoundary
- ErrorFallback

## Best Practices

1. Keep components focused and single-responsibility
2. Use TypeScript for type safety
3. Implement proper error handling
4. Follow accessibility guidelines
5. Maintain consistent naming conventions
6. Document complex components
7. Write unit tests for critical components 