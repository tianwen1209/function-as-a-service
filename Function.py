from Application import Application
class Function:
    def __init__(self, function_id, app_id, start_time, trigger, function_duration, function_memory):
        self.function_id = function_id
        self.app_id = app_id
        self.start_time = start_time
        self.trigger = trigger
        self.function_duration = function_duration
        self.function_memory = function_memory
        self.end_time = self.start_time+self.function_duration
        self.app = Application(self.app_id)






