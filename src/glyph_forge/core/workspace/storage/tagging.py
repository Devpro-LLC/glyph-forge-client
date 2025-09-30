# tagging.py
import uuid, datetime as dt
def new_run_id() -> str:
    return dt.datetime.now().strftime("%Y%m%dT%H%M%S") + "_" + str(uuid.uuid4())[:8]
