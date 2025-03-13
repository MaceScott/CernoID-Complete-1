'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';

interface QueryConfig<T> {
  key: string;
  fetchFn: () => Promise<T>;
  staleTime?: number;
  cacheTime?: number;
  retryCount?: number;
  retryDelay?: number;
  onError?: (error: Error) => void;
  onSuccess?: (data: T) => void;
}

interface QueryState<T> {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
  isStale: boolean;
}

// Global cache for query results
const queryCache = new Map<
  string,
  { data?: any; timestamp: number; promise?: Promise<any> }
>();

export function useOptimizedQuery<T>({
  key,
  fetchFn,
  staleTime = 30000, // 30 seconds
  cacheTime = 300000, // 5 minutes
  retryCount = 3,
  retryDelay = 1000,
  onError,
  onSuccess,
}: QueryConfig<T>): QueryState<T> & { refetch: () => Promise<void> } {
  const [state, setState] = useState<QueryState<T>>({
    data: null,
    error: null,
    isLoading: true,
    isStale: false,
  });

  const retryCountRef = useRef(0);
  const router = useRouter();

  // Clean up expired cache entries
  useEffect(() => {
    const cleanup = setInterval(() => {
      const now = Date.now();
      queryCache.forEach((value, key) => {
        if (now - value.timestamp > cacheTime) {
          queryCache.delete(key);
        }
      });
    }, 60000); // Clean up every minute

    return () => clearInterval(cleanup);
  }, [cacheTime]);

  const fetchData = useCallback(async (isRefetch = false) => {
    try {
      const cached = queryCache.get(key);
      const now = Date.now();

      if (!isRefetch && cached?.data) {
        if (cached.promise) {
          const data = await cached.promise;
          setState((prev) => ({
            ...prev,
            data,
            isLoading: false,
            error: null,
          }));
          return;
        }

        if (now - cached.timestamp < staleTime) {
          setState((prev) => ({
            ...prev,
            data: cached.data,
            isLoading: false,
            error: null,
            isStale: false,
          }));
          return;
        }

        setState((prev) => ({
          ...prev,
          data: cached.data,
          isStale: true,
        }));
      }

      const promise = fetchFn();
      queryCache.set(key, {
        timestamp: now,
        promise,
      });

      const data = await promise;
      queryCache.set(key, {
        data,
        timestamp: now,
      });

      setState({
        data,
        error: null,
        isLoading: false,
        isStale: false,
      });

      onSuccess?.(data);
      retryCountRef.current = 0;
    } catch (error) {
      const isAuthError = error instanceof Error && 
        (error.message.includes('unauthorized') || error.message.includes('unauthenticated'));

      if (isAuthError) {
        // Redirect to login for auth errors
        router.push('/login');
        return;
      }

      if (retryCountRef.current < retryCount) {
        // Retry with exponential backoff
        retryCountRef.current++;
        const delay = retryDelay * Math.pow(2, retryCountRef.current - 1);
        setTimeout(() => fetchData(isRefetch), delay);
        return;
      }

      setState((prev) => ({
        ...prev,
        error: error as Error,
        isLoading: false,
      }));

      onError?.(error as Error);
      queryCache.delete(key);
    }
  }, [
    key,
    fetchFn,
    staleTime,
    retryCount,
    retryDelay,
    onError,
    onSuccess,
    router,
  ]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = useCallback(() => fetchData(true), [fetchData]);

  return {
    ...state,
    refetch,
  };
} 