export const logger = {
    error: (message: string, error: any) => {
        console.error(`[ERROR] ${message}`, error);
    },
    info: (message: string) => {
        console.log(`[INFO] ${message}`);
    },
    warn: (message: string) => {
        console.warn(`[WARN] ${message}`);
    },
}; 