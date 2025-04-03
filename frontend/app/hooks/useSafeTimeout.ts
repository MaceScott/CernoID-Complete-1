import { useEffect, useRef } from 'react';

export const useSafeTimeout = () => {
    const timeoutRefs = useRef<number[]>([]);

    useEffect(() => {
        return () => {
            // Cleanup all timeouts on unmount
            timeoutRefs.current.forEach((timeoutId) => {
                window.clearTimeout(timeoutId);
            });
        };
    }, []);

    const safeSetTimeout = (callback: () => void, delay: number) => {
        const timeoutId = window.setTimeout(callback, delay);
        timeoutRefs.current.push(timeoutId);
        return timeoutId;
    };

    const safeClearTimeout = (timeoutId: number) => {
        window.clearTimeout(timeoutId);
        timeoutRefs.current = timeoutRefs.current.filter((id) => id !== timeoutId);
    };

    return {
        safeSetTimeout,
        safeClearTimeout,
    };
};

export const useSafeInterval = () => {
    const intervalRefs = useRef<number[]>([]);

    useEffect(() => {
        return () => {
            // Cleanup all intervals on unmount
            intervalRefs.current.forEach((intervalId) => {
                window.clearInterval(intervalId);
            });
        };
    }, []);

    const safeSetInterval = (callback: () => void, delay: number) => {
        const intervalId = window.setInterval(callback, delay);
        intervalRefs.current.push(intervalId);
        return intervalId;
    };

    const safeClearInterval = (intervalId: number) => {
        window.clearInterval(intervalId);
        intervalRefs.current = intervalRefs.current.filter((id) => id !== intervalId);
    };

    return {
        safeSetInterval,
        safeClearInterval,
    };
}; 