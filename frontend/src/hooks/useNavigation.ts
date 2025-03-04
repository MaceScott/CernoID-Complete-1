import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

interface NavigationState {
  currentPath: string;
  previousPath: string | null;
  isNavigating: boolean;
}

interface UseNavigationReturn {
  navigationState: NavigationState;
  navigate: (path: string) => void;
  goBack: () => void;
  goForward: () => void;
}

export const useNavigation = (): UseNavigationReturn => {
  const navigate = useNavigate();
  const [navigationState, setNavigationState] = useState<NavigationState>({
    currentPath: window.location.pathname,
    previousPath: null,
    isNavigating: false,
  });

  const handleNavigate = useCallback((path: string) => {
    setNavigationState(prev => ({
      ...prev,
      previousPath: prev.currentPath,
      currentPath: path,
      isNavigating: true,
    }));
    navigate(path);
  }, [navigate]);

  const handleGoBack = useCallback(() => {
    if (navigationState.previousPath) {
      setNavigationState(prev => ({
        ...prev,
        currentPath: prev.previousPath!,
        previousPath: null,
        isNavigating: true,
      }));
      navigate(-1);
    }
  }, [navigate, navigationState.previousPath]);

  const handleGoForward = useCallback(() => {
    setNavigationState(prev => ({
      ...prev,
      isNavigating: true,
    }));
    navigate(1);
  }, [navigate]);

  return {
    navigationState,
    navigate: handleNavigate,
    goBack: handleGoBack,
    goForward: handleGoForward,
  };
}; 