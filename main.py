# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, HTMLResponse
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

def time_stream(interval: float = 1.0):
    """
    無限迴圈回傳目前時間字串。
    """
    while True:
        yield f"{datetime.now().isoformat()}\n"
        time.sleep(interval)

# GET /time: 顯示即時時間的簡易網頁。
@app.get("/time")
def time_page():
    html = """
    <html>
        <head>
            <title>Now</title>
            <style>
                body { font-family: sans-serif; background: #111; color: #0f0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                #time { font-size: 2rem; white-space: pre; }
            </style>
        </head>
        <body>
            <div id="time">loading...</div>
            <script>
                const target = document.getElementById("time");
                async function start() {
                    const response = await fetch("/time/stream");
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let buffer = "";
                    while (true) {
                        const { value, done } = await reader.read();
                        if (done) break;
                        buffer += decoder.decode(value, { stream: true });
                        const parts = buffer.split("\n");
                        buffer = parts.pop() ?? "";
                        const latest = parts.filter(Boolean).pop();
                        if (latest) {
                            target.textContent = latest;
                        }
                    }
                }
                start();
            </script>
        </body>
    </html>
    """
    return HTMLResponse(html)

# GET /time/stream: 以串流方式持續送出現在時間。
@app.get("/time/stream")
def stream_time():
    """
    以串流方式持續送出現在時間。
    """
    return StreamingResponse(time_stream(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
