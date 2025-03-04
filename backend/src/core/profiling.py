import memory_profiler
import psutil

def monitor_memory():
    process = psutil.Process()
    memory_info = process.memory_info()
    logger.info(
        "Memory usage",
        rss=memory_info.rss / 1024 / 1024,  # MB
        vms=memory_info.vms / 1024 / 1024   # MB
    ) 