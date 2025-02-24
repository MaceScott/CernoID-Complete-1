import React, { 
    createContext, 
    useContext, 
    useReducer, 
    useEffect 
} from 'react';
import { User, AppSettings, Theme } from '../types';

interface AppState {
    user: User | null;
    settings: AppSettings | null;
    theme: Theme;
    isInitialized: boolean;
}

type AppAction = 
    | { type: 'SET_USER'; payload: User | null }
    | { type: 'SET_SETTINGS'; payload: AppSettings }
    | { type: 'SET_THEME'; payload: Theme }
    | { type: 'SET_INITIALIZED'; payload: boolean };

interface AppContextType extends AppState {
    dispatch: React.Dispatch<AppAction>;
}

const initialState: AppState = {
    user: null,
    settings: null,
    theme: 'light',
    isInitialized: false
};

const AppContext = createContext<AppContextType | undefined>(undefined);

const appReducer = (state: AppState, action: AppAction): AppState => {
    switch (action.type) {
        case 'SET_USER':
            return {
                ...state,
                user: action.payload
            };
        case 'SET_SETTINGS':
            return {
                ...state,
                settings: action.payload
            };
        case 'SET_THEME':
            return {
                ...state,
                theme: action.payload
            };
        case 'SET_INITIALIZED':
            return {
                ...state,
                isInitialized: action.payload
            };
        default:
            return state;
    }
};

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ 
    children 
}) => {
    const [state, dispatch] = useReducer(appReducer, initialState);

    useEffect(() => {
        const initializeApp = async () => {
            try {
                // Load user preferences from localStorage
                const savedTheme = localStorage.getItem('theme') as Theme;
                if (savedTheme) {
                    dispatch({ type: 'SET_THEME', payload: savedTheme });
                }

                // Check authentication status
                const token = localStorage.getItem('token');
                if (token) {
                    try {
                        const response = await fetch('/api/auth/me', {
                            headers: {
                                Authorization: `Bearer ${token}`
                            }
                        });
                        if (response.ok) {
                            const user = await response.json();
                            dispatch({ type: 'SET_USER', payload: user });
                        }
                    } catch (error) {
                        console.error('Auth check failed:', error);
                        localStorage.removeItem('token');
                    }
                }

                // Load app settings
                try {
                    const response = await fetch('/api/settings');
                    if (response.ok) {
                        const settings = await response.json();
                        dispatch({ type: 'SET_SETTINGS', payload: settings });
                    }
                } catch (error) {
                    console.error('Failed to load settings:', error);
                }

            } finally {
                dispatch({ type: 'SET_INITIALIZED', payload: true });
            }
        };

        initializeApp();
    }, []);

    // Save theme preference when it changes
    useEffect(() => {
        localStorage.setItem('theme', state.theme);
    }, [state.theme]);

    return (
        <AppContext.Provider value={{ ...state, dispatch }}>
            {children}
        </AppContext.Provider>
    );
};

export const useApp = () => {
    const context = useContext(AppContext);
    if (context === undefined) {
        throw new Error('useApp must be used within an AppProvider');
    }
    return context;
}; 