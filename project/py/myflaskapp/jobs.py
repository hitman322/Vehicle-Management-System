from apscheduler.schedulers.blocking import BlockingScheduler
from app import schedule_job

sched = BlockingScheduler()


@sched.scheduled_job('cron', day_of_week='mon-sun', hour=23, minute=56)
def scheduled_job():
	schedule_job()


sched.start()