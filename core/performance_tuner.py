import psutil

def get_optimal_ram():
    total = psutil.virtual_memory().total // (1024 * 1024)
    return max(1024, int(total * 0.5))  # 50% of total RAM

def get_optimized_flags(ram_mb):
    return [
        f"-Xms{ram_mb}M",
        f"-Xmx{ram_mb}M",
        "-XX:+UseG1GC",
        "-XX:+ParallelRefProcEnabled",
        "-XX:MaxGCPauseMillis=200"
    ]
