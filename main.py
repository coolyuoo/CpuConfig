from fastapi import FastAPI
import time, os, multiprocessing as mp
import math
import uvicorn

app = FastAPI(title="CPU Demo (simple)")

def burn_cpu_seconds(seconds: float) -> float:
    target = time.process_time() + seconds
    x = 0.0
    while time.process_time() < target:
        x = x * 1.0000001 + 1.0
    return x

def worker(seconds: float):
    burn_cpu_seconds(seconds)

@app.get("/")
def root():
    return {"ok": True, "usage": "GET /burn/{cpu_seconds}  ，環境變數 PROCS 控制同時進程數（預設1）"}

@app.get("/burn")
def burn(sec: float = 3.0):
    t0 = time.perf_counter()
    # 單執行緒 busy loop（Python GIL 反而剛好：一條線就能吃滿 quota）
    x = 0.0
    while time.perf_counter() - t0 < sec:
        # 做點浮點運算避免被最佳化
        x += math.sin(x) * math.cos(x) + math.sqrt(12345.6789)
    return {"ok": True, "wall_seconds": time.perf_counter() - t0}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), workers=1)
