from app.models import *
from app import db
from datetime import datetime
from pytz import timezone
from .commons import *
import time

class TaskUtil(object):

    @staticmethod
    def get_task_name(session, result_id):
        return '{}@{}#{}'.format(session.name, session.algorithm, result_id)

    @staticmethod
    def save_execution_time(module, start_ts, fn, result_id=None):
        end_ts = time.time()
        exec_time = end_ts - start_ts
        start_time = datetime.fromtimestamp(int(start_ts), timezone(TIME_ZONE))
        db.session.add(ExecutionTime(module=module, function=fn, tag="",
                                     start_time=start_time, execution_time=exec_time, result_id=result_id))
        return exec_time