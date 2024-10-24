import datetime
from datetime import timedelta, datetime

def delete_old_entries(history):
    """delete old entries from conversation"""
    seven_days_ago = (datetime.now() - timedelta(days=7)).timestamp()
    history.delete(
        where={"timestamp": {"$lt": seven_days_ago}}
    )