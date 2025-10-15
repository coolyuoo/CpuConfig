from fastapi import FastAPI
import time, os, multiprocessing as mp
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

@app.get("/burn/{cpu_seconds}")
def burn(cpu_seconds: float):
    # 只保留一個參數：cpu_seconds
    procs = int(os.getenv("PROCS", "1"))
    procs = max(1, min(procs, os.cpu_count() or 64))

    start = time.perf_counter()
    if procs == 1:
        _ = burn_cpu_seconds(cpu_seconds)
    else:
        with mp.Pool(processes=procs) as pool:
            pool.map(worker, [cpu_seconds] * procs)
    wall = time.perf_counter() - start

    return {
        "cpu_seconds_per_proc": cpu_seconds,
        "processes_used": procs,
        "wall_time_seconds": round(wall, 3),
        "note": "只輸入一個參數。要示範多核，改環境變數 PROCS；要示範限速，用 --cpus。",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), workers=1)
