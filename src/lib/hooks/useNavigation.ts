import { useCallback } from 'react';
import { useRouter } from 'next/router';

export const useNavigation = () => {
  const router = useRouter();

  const navigate = useCallback((path: string) => {
    router.push(path);
  }, [router]);

  return {
    navigate,
    currentPath: router.pathname
  };
}; 