#! coding:utf-8
"""
"""
import datetime
import glob
import json
import os
from functools import wraps
import subprocess
import platform

from flask import Flask, Response, jsonify, request, abort, url_for, render_template

from common_tools import StatusCodes, ContentType, JobState, ResultState
from models import db, Task

""" Application """
app = Flask(__name__)
""" Settings """
app.config.from_object('config.DevelopmentConfig')
""" Database """
app.config['SQLALCHEMY_DATABASE_URI'] = app.config["DATABASE_URI"]
db.init_app(app)
db.app = app
db.create_all()
with app.app_context():
    db.create_all()

""" Background Process"""
backgraoud_proc = None
running_proc_name = None

""" cron """
from common_tools import Scheduler

if not os.path.exists(os.path.join(app.root_path, 'projects')):
    raise IOError("app.root_path is invalid => {}".format(app.root_path))


def get_setting_jsons() -> list:
    trainer_path = os.path.join(app.root_path, 'projects', '*', '*', 'setting.conf')
    settings = glob.glob(trainer_path, recursive=True)
    return settings


def cron_func():
    print(".")

    global backgraoud_proc, running_proc_name

    # Scan Setting.conf
    setting_list = get_setting_jsons()
    for setting_path in setting_list:

        # FulPath Parsing
        param_dir, _ = setting_path.rsplit("/", 1)
        model_dir, param_id = param_dir.rsplit("/", 1)
        project_dir, model_id = model_dir.rsplit("/", 1)

        # Check OverWrite
        name = Task.craete_name(model_id, param_id)

        # Create New
        worker = Task(name)
        worker.model_dir = model_dir
        worker.param_dir = param_dir
        d = worker.to_dict()
        model_set(name, d)

    if backgraoud_proc is not None:
        if backgraoud_proc.poll() is None:  # Process not finished.
            print("is running : " + running_proc_name)
            return
        else:
            stdout = "".join([s.decode("utf-8") for s in backgraoud_proc.stdout.readlines()])
            stderr = "".join([s.decode("utf-8") for s in backgraoud_proc.stderr.readlines()])
            if stdout != "":  app.logger.debug(stdout)
            if stderr != "":  app.logger.debug(stderr)

            backgraoud_proc.terminate()
            backgraoud_proc = None

            # Status Update
            finished_task = model_get(running_proc_name)
            finished_task.job_state = JobState.Stopping
            finished_task.result_state = ResultState.Success
            model_set(running_proc_name, finished_task.to_dict())

            finished_dict = finished_task.to_dict()

            print("=> Finished: {},{},{}".format(name, finished_dict["result_state"], finished_dict["job_state"]))
            return

    # Select Waiting Task
    queryes = [query for query in model_get_all()]

    for task_query in queryes:
        if task_query.job_state != JobState.Stopping:
            continue

        assert task_query.job_state == JobState.Stopping, task_query.job_state

        if task_query.result_state != ResultState.unexecuted:
            continue

        if backgraoud_proc is not None:
            continue

        print("=> Run: {}, {}, {}".format(name, task_query.result_state, task_query.job_state))

        # Working Dirs
        model_dir = task_query.model_dir
        param_dir = task_query.param_dir

        # Exist Test
        trainer_py = os.path.join(model_dir, "trainer.py")
        assert os.path.exists(trainer_py)

        # Run!
        args = ["python", "trainer.py", "--ini", os.path.join(param_dir, "_setting.conf")]
        running_proc_name = name
        backgraoud_proc = subprocess.Popen(args,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           cwd=model_dir,
                                           close_fds=False if platform.system() == 'Windows' else True,
                                           )
        # state update
        task_query.job_state = JobState.Running
        d = task_query.to_dict()
        model_set(name, d)


cron = Scheduler(sleep_time=app.config["CRON_INTERVAL_SEC"], func=cron_func)

""" Utils """


def consumes(content_type):
    """Content-Type Checker"""

    def _consumes(fun):
        @wraps(fun)
        def __consumes(*argv, **keywords):
            if request.headers['Content-Type'] != content_type:
                abort(StatusCodes.BadRequest400)
            return fun(*argv, **keywords)

        return __consumes

    return _consumes


def make_dir(dir: str):
    try:
        if not os.path.exists(dir):
            os.mkdir(dir)
    except Exception:
        pass


""" Initialize """


def app_init():
    make_dir(app.config["DB_DIR"])


""" Health Check """


@app.route('/health', methods=['GET', 'POST'])
def health():
    """ Health CHeck API"""

    response = jsonify({'health check': 'success'})
    response.status_code = StatusCodes.OK200
    return response


""" Health Check """


@app.route('/')
def status():
    """ Status Page"""

    _tasks = Task.query.all()
    assert type(_tasks) == list

    app.logger.debug(_tasks)

    if _tasks is None:
        tasks = []
    else:
        tasks = [t.to_dict() for t in _tasks]
    return render_template('status.html', results=tasks)


""" REST API """


@app.route('/api/<key>', methods=["GET"])
def rest_get(key):
    # Load Model data
    tasks = model_get(key)

    if tasks is None:
        response = Response()
        response.status_code = StatusCodes.NoContent
        return response
    else:
        response = jsonify(tasks)
        response.status_code = StatusCodes.OK200
        return response


@app.route('/api/<key>', methods=["POST"])
@consumes(ContentType.application_json)
def rest_post(key):
    # Json Encode -> to Dict
    content_body_dict = json.loads(request.data.decode("utf-8"))
    assert type(content_body_dict) == dict

    # Save data for model
    model_set(key, content_body_dict)

    # Create Resoponse Objects
    response = jsonify(content_body_dict)
    response.status_code = StatusCodes.created
    response.headers['Location'] = url_for('rest_get', key=key)
    return response


@app.route('/api/<key>', methods=['DELETE'])
def rest_delete(key):
    model_delete(key)

    response = Response()
    response.status_code = StatusCodes.OK200
    return response


""" Model Accessors"""


def _model_update(key: str, values: dict):
    assert type(values) == dict

    task = Task.query.filter_by(name=key).first()
    task.update(values)
    task.update_last_update()
    db.session.commit()


def model_set(key: str, values: dict):
    assert type(values) == dict
    tasks = Task.query.filter_by(name=key).first()

    if tasks is None:
        task = Task(key)
        task.update(values)
        db.session.add(task)
        db.session.commit()
    else:
        _model_update(key, values)


def model_get_all():
    return Task.query.all()


def model_get(key: str):
    tasks = Task.query.filter_by(name=key).first()
    return tasks


def model_has_key(key: str) -> bool:
    tasks = Task.query.filter_by(name=key).first()
    if tasks is None:
        return False
    else:
        return True


def model_delete(key: str):
    task = Task.query.filter_by(name=key).first()
    db.session.delete(task)
    db.session.commit()


# =========================================
# Multiplocess
# =========================================
@app.route('/api/process/numbers', methods=['POST'])
def process_numbers():
    # mock
    process_num = 0
    response = jsonify({"numbers": process_num})
    response.status_code = StatusCodes.OK200
    return response


@app.route('/api/process/killall', methods=['POST'])
def process_kill_all():
    # mock
    response = Response()
    response.status_code = StatusCodes.OK200
    return response


if __name__ == '__main__':
    cron.start()
    app_init()
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
        use_reloader=False
    )

    cron.stop()

    # app.db.save()
