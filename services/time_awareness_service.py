from datetime import datetime


class TimeAwarenessService:
    init_time = None

    def __init__(self):
        self.init_time = datetime.now()

    def get_seconds_since(self, time):
        return (datetime.now() - time).total_seconds()

    def get_hours_since(self, time):
        return self.get_seconds_since(time) / 3600

    def get_days_since(self, time):
        return self.get_hours_since(time) / 24

    def get_adaptive_time_since(self, time):
        seconds = self.get_seconds_since(time)
        if seconds < 60:
            return f"{seconds:.2f} seconds"
        elif seconds < 3600:
            return f"{seconds / 60:.2f} minutes"
        elif seconds < 86400:
            return f"{seconds / 3600:.2f} hours"
        else:
            return f"{seconds / 86400:.2f} days"
