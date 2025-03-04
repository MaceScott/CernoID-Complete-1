import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { AppRoutes } from './routes';
import { ErrorBoundary } from './components/ErrorBoundary/ErrorBoundary';

const App: React.FC = () => {
    return (
        <ErrorBoundary>
            <AppProvider>
                <BrowserRouter>
                    <AppRoutes />
                </BrowserRouter>
            </AppProvider>
        </ErrorBoundary>
    );
};

export default App; 