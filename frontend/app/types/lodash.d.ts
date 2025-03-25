declare module 'lodash/debounce' {
    interface DebouncedFunction<T extends (...args: any[]) => any> extends Function {
        (...args: Parameters<T>): ReturnType<T>;
        cancel(): void;
        flush(): ReturnType<T>;
    }

    const debounce: <T extends (...args: any[]) => any>(
        func: T,
        wait?: number,
        options?: {
            leading?: boolean;
            trailing?: boolean;
            maxWait?: number;
        }
    ) => DebouncedFunction<T>;

    export default debounce;
} 