import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { User } from '../types/user';
import { AppSettings } from '../types/settings';

interface AppState {
    user: User | null;
    settings: AppSettings | null;
    theme: 'light' | 'dark';
    isInitialized: boolean;
}

type AppAction = 
    | { type: 'SET_USER'; payload: User | null }
    | { type: 'SET_SETTINGS'; payload: AppSettings }
    | { type: 'SET_THEME'; payload: 'light' | 'dark' }
    | { type: 'SET_INITIALIZED'; payload: boolean };

interface AppContextType {
    state: AppState;
    dispatch: React.Dispatch<AppAction>;
    user: User | null;
    isInitialized: boolean;
}

const initialState: AppState = {
    user: null,
    settings: null,
    theme: 'light',
    isInitialized: false
};

const AppContext = createContext<AppContextType | undefined>(undefined);

function appReducer(state: AppState, action: AppAction): AppState {
    switch (action.type) {
        case 'SET_USER':
            return { ...state, user: action.payload };
        case 'SET_SETTINGS':
            return { ...state, settings: action.payload };
        case 'SET_THEME':
            return { ...state, theme: action.payload };
        case 'SET_INITIALIZED':
            return { ...state, isInitialized: action.payload };
        default:
            return state;
    }
}

export function AppProvider({ children }: { children: ReactNode }) {
    const [state, dispatch] = useReducer(appReducer, initialState);

    const value = {
        state,
        dispatch,
        user: state.user,
        isInitialized: state.isInitialized
    };

    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    );
}

export function useApp() {
    const context = useContext(AppContext);
    if (context === undefined) {
        throw new Error('useApp must be used within an AppProvider');
    }
    return context;
} 