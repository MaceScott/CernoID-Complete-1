import { Route } from 'react-router-dom';

interface NavigationNode {
    path: string;
    component: string;
    requiredRole?: string;
    requiredPermissions?: string[];
    children?: NavigationNode[];
}

const navigationMap: NavigationNode[] = [
    {
        path: '/login',
        component: 'Login'
    },
    {
        path: '/dashboard',
        component: 'Dashboard',
        children: [
            {
                path: '/recognition',
                component: 'Recognition'
            },
            {
                path: '/users',
                component: 'UserManagement',
                requiredRole: 'admin',
                requiredPermissions: ['manage_users']
            },
            {
                path: '/settings',
                component: 'Settings',
                requiredRole: 'admin',
                requiredPermissions: ['manage_settings']
            }
        ]
    }
];

export const validateNavigation = () => {
    const issues: string[] = [];
    
    // Check for orphaned routes
    const allPaths = new Set(navigationMap.flatMap(node => 
        getAllPaths(node)
    ));
    
    // Verify all routes have proper transitions
    navigationMap.forEach(node => {
        validateNode(node, allPaths, issues);
    });
    
    return issues;
};

const getAllPaths = (node: NavigationNode): string[] => {
    const paths = [node.path];
    if (node.children) {
        paths.push(...node.children.flatMap(child => getAllPaths(child)));
    }
    return paths;
};

const validateNode = (
    node: NavigationNode,
    allPaths: Set<string>,
    issues: string[]
) => {
    // Check for proper parent route
    if (node.path !== '/login' && !node.path.startsWith('/dashboard')) {
        issues.push(`Route ${node.path} is not properly nested under parent`);
    }
    
    // Check for permission consistency
    if (node.requiredRole && !node.requiredPermissions) {
        issues.push(`Route ${node.path} has role but no permissions defined`);
    }
    
    // Validate children
    if (node.children) {
        node.children.forEach(child => {
            validateNode(child, allPaths, issues);
        });
    }
}; 