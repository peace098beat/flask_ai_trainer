import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Task(db.Model):
    """
    http://flask-sqlalchemy.pocoo.org/2.1/queries/
    """
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(80), unique=True)

    job_state = db.Column(db.String(20))
    result_state = db.Column(db.String(20))
    param_dir = db.Column(db.String(256))
    model_dir = db.Column(db.String(256))

    loss = db.Column(db.String(100))
    accuracy = db.Column(db.String(100))
    epoch = db.Column(db.String(100))
    elapsed = db.Column(db.String(100))

    created = db.Column(db.String(30))
    last_update = db.Column(db.String(30))

    def __init__(self, name):
        self.name = name
        self.created = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.job_state = "stopping"
        self.result_state = "unexecuted"

    def __repr__(self):
        return '<Task %r>' % self.name

    def to_dict(self):
        d = self.__dict__
        d.pop('_sa_instance_state', None)
        sorted(d.items(), key=lambda x: x[0])
        return d

    def update(self, values_dict: dict):
        for key, value in values_dict.items():
            if key == "name":
                continue
            else:
                setattr(self, key, value)

    def update_last_update(self):
        self.last_update = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def craete_name(model_name: str, param_name: str):
        return model_name + "-" + param_name
