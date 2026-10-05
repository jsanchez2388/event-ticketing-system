# Cache Benchmark Results

Event 103, 30 timed runs per arm, measured with time.perf_counter().

| Metric | Database (new connection) | Redis cache | Database (open connection) |
|---|---|---|---|
| Minimum | 387.950 ms | 0.530 ms | 111.398 ms |
| Maximum | 1423.282 ms | 1.345 ms | 403.245 ms |
| Average | 504.879 ms | 0.947 ms | 123.627 ms |
| Median | 404.717 ms | 0.934 ms | 113.918 ms |
| Std dev | 262.650 ms | 0.189 ms | 52.837 ms |
