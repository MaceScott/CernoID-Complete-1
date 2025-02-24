// Centralized route management
export const routes = {
  auth: {
    login: '/login',
    logout: '/logout',
  },
  dashboard: {
    home: '/',
    review: '/review',
    alerts: '/alerts',
  },
  admin: {
    root: '/admin',
    users: '/admin/users',
    cameras: '/admin/cameras',
  },
  settings: '/settings',
} as const

export const pageRegistry = {
  [routes.auth.login]: {
    title: 'Login',
    public: true,
  },
  [routes.dashboard.home]: {
    title: 'Dashboard',
    roles: ['admin', 'user'],
  },
  [routes.dashboard.review]: {
    title: 'Camera Review',
    roles: ['admin', 'user'],
  },
  [routes.dashboard.alerts]: {
    title: 'Alerts',
    roles: ['admin', 'user'],
  },
  [routes.admin.root]: {
    title: 'Admin Dashboard',
    roles: ['admin'],
  },
  [routes.admin.users]: {
    title: 'User Management',
    roles: ['admin'],
  },
  [routes.admin.cameras]: {
    title: 'Camera Management',
    roles: ['admin'],
  },
  [routes.settings]: {
    title: 'Settings',
    roles: ['admin', 'user'],
  },
} as const 