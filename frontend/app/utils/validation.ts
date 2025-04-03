export interface ValidationResult {
    isValid: boolean;
    errors: string[];
}

export const validateEmail = (email: string): ValidationResult => {
    const errors: string[] = [];
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!email) {
        errors.push('Email is required');
    } else if (!emailRegex.test(email)) {
        errors.push('Invalid email format');
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
};

export const validatePassword = (password: string): ValidationResult => {
    const errors: string[] = [];
    
    if (!password) {
        errors.push('Password is required');
    } else {
        if (password.length < 8) {
            errors.push('Password must be at least 8 characters long');
        }
        if (!/[A-Z]/.test(password)) {
            errors.push('Password must contain at least one uppercase letter');
        }
        if (!/[a-z]/.test(password)) {
            errors.push('Password must contain at least one lowercase letter');
        }
        if (!/[0-9]/.test(password)) {
            errors.push('Password must contain at least one number');
        }
        if (!/[!@#$%^&*]/.test(password)) {
            errors.push('Password must contain at least one special character (!@#$%^&*)');
        }
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
};

export const validateUsername = (username: string): ValidationResult => {
    const errors: string[] = [];
    const usernameRegex = /^[a-zA-Z0-9_-]{3,20}$/;
    
    if (!username) {
        errors.push('Username is required');
    } else if (!usernameRegex.test(username)) {
        errors.push('Username must be 3-20 characters long and can only contain letters, numbers, underscores, and hyphens');
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
};

export const validateURL = (url: string): ValidationResult => {
    const errors: string[] = [];
    
    if (!url) {
        errors.push('URL is required');
    } else {
        try {
            new URL(url);
        } catch {
            errors.push('Invalid URL format');
        }
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
};

export const validateFile = (file: File, maxSize: number = 5 * 1024 * 1024): ValidationResult => {
    const errors: string[] = [];
    
    if (!file) {
        errors.push('File is required');
    } else {
        if (file.size > maxSize) {
            errors.push(`File size must be less than ${maxSize / (1024 * 1024)}MB`);
        }
        
        // Add more file validation as needed (type, extension, etc.)
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
};

export const sanitizeInput = (input: string): string => {
    return input
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;')
        .replace(/\//g, '&#x2F;');
}; 