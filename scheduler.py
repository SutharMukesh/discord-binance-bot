import schedule
import time
from main import start


def job():
    print("I'm working...")
    start()


schedule.every(1).minute.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
