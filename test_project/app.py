import random
import time

from celery import Celery

app = Celery(
    "tests",
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)
app.conf.broker_connection_retry_on_startup = True
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True
app.conf.task_track_started = True
app.conf.result_extended = True
app.conf.enable_utc = True


@app.task()
def order_workflow():
    time.sleep(random.randrange(1, 5))
    update_inventory.apply_async()
    create_invoice.apply_async()


@app.task()
def create_invoice():
    time.sleep(random.randrange(1, 5))


@app.task()
def update_inventory():
    time.sleep(random.randrange(1, 5))
    create_shipment.apply_async(countdown=10)


@app.task()
def create_shipment():
    time.sleep(random.randrange(1, 5))
    generate_sales_report.apply_async()
    notify_user.apply_async()


@app.task()
def generate_sales_report():
    time.sleep(random.randrange(1, 5))


@app.task()
def notify_user():
    time.sleep(random.randrange(1, 5))
