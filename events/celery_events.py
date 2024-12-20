import time
from celery import Celery
from celery.events import EventReceiver
from celery.events.state import State
from celery.signals import worker_ready, worker_shutdown

# 配置 Celery
app = Celery('test', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')


# 设置监听事件处理
def handle_event(event):
    """
    处理 Celery 事件
    """
    event_type = event.get('type')

    # 监听 worker 上线事件
    if event_type == 'worker-online':
        print(f"Worker {event['hostname']} has come online.")

    # 监听 worker 下线事件
    elif event_type == 'worker-offline':
        print(f"Worker {event['hostname']} has gone offline.")

    # 监听任务成功事件
    elif event_type == 'task-succeeded':
        print(f"Task {event['uuid']} succeeded with result: {event.get('result')}")

    # 监听任务失败事件
    elif event_type == 'task-failed':
        print(f"Task {event['uuid']} failed with error: {event.get('exception')}")

    # 其他类型事件
    else:
        print(f"Received event: {event}")


# 启动事件监听
def start_event_listener():
    print("Starting Celery event listener...")

    # 创建事件接收器
    with app.connection() as connection:
        state = State()
        receiver = EventReceiver(connection, handlers={'*': handle_event})

        # 持续监听
        while True:
            receiver.capture(limit=None, timeout=10)  # 每1秒检查一次事件
            time.sleep(1)


# 启动 Celery 事件监听器
if __name__ == '__main__':
    start_event_listener()
