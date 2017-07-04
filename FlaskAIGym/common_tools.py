from threading import Timer


class StatusCodes:
    OK200 = 200
    created = 201
    BadRequest400 = 400
    NoContent = 204


class ContentType:
    text_plain = 'text/plain'
    application_json = 'application/json'


class JobState:
    Running = "running"
    Stopping = "stopping"


class ResultState:
    unexecuted = "unexecuted"
    Success = "success"
    ErrorFinished = "error finished"


class Scheduler(object):
    """
    Flask Cron Timer
    https://gist.github.com/chadselph/4ff85c8c4f68aa105f4b
    """

    def __init__(self, sleep_time, func):
        self.sleep_time = sleep_time
        self.function = func
        self._t = None

    def start(self):
        if self._t is None:
            self._t = Timer(self.sleep_time, self._run)
            self._t.start()
        else:
            raise Exception("this timer is already running")

    def _run(self):
        self.function()
        self._t = Timer(self.sleep_time, self._run)
        self._t.start()

    def stop(self):
        if self._t is not None:
            self._t.cancel()
            self._t = None
