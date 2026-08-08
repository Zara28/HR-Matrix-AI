from prometheus_client import Gauge, Counter, Histogram

# Инфраструктурный уровень
SYSTEM_CPU_USAGE = Gauge("system_cpu_usage_percent", "System CPU usage percent")
SYSTEM_RAM_USAGE = Gauge("system_ram_usage_percent", "System RAM usage percent")

# Компонентный уровень
ACTIVE_WORKERS = Gauge("active_workers_count", "Active workers count")
PROCESSED_CODE_BYTES = Counter("processed_code_bytes_total", "Total processed code bytes")

# Уровень SLA
INFERENCE_TIME = Histogram("inference_time_seconds", "Inference time in seconds")
TOTAL_PROCESSING_TIME = Histogram("total_processing_time_seconds", "Total survey processing time")