# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from fastapi import FastAPI, Query
from threading import Thread, Event
import time
import uvicorn

try:
    import psutil  # type: ignore
except ImportError:
    psutil = None

app = FastAPI()

# 用來控制 CPU 壓力的事件旗標與執行緒
cpu_event = Event()
cpu_thread = None


def cpu_stress(percent: int, stop_event: Event):
    """
    根據 percent 製造指定百分比的 CPU 負載
    """
    period = 0.1  # 每次循環的總時間 (秒)
    busy_time = period * percent / 100.0  # 忙碌時間
    idle_time = period - busy_time        # 休息時間

    while not stop_event.is_set():
        start = time.time()
        # 忙碌段
        while (time.time() - start) < busy_time:
            pass  # busy loop
        # 休息段
        time.sleep(idle_time)


@app.get("/cpu")
def set_cpu(percent: int = Query(..., ge=1, le=100)):
    """
    啟動指定百分比的 CPU 壓力
    """
    global cpu_thread, cpu_event

    if cpu_thread and cpu_thread.is_alive():
        return {"status": "already running"}

    cpu_event.clear()
    cpu_thread = Thread(target=cpu_stress, args=(percent, cpu_event))
    cpu_thread.start()
    return {"status": "started", "percent": percent}


@app.get("/cpu/stop")
def stop_cpu():
    """
    停止 CPU 壓力測試
    """
    global cpu_thread, cpu_event

    if cpu_thread and cpu_thread.is_alive():
        cpu_event.set()
        cpu_thread.join()
        return {"status": "stopped"}

    return {"status": "not running"}


@app.get("/")
def cpu_usage():
    """
    量測最近一秒 CPU 使用率
    """
    if psutil is None:
        return {"cpu_percent": None}
    percent = psutil.cpu_percent(interval=1.0)
    return {"cpu_percent": percent}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
