class Config(object):
    DEBUG = False
    TESTING = False
    DB_DIR = "db"
    DATABASE_URI = 'sqlite:///db/app.db'  # 'sqlite:///:memory:'
    HOST = "0.0.0.0"
    PORT = 5000
    CRON_INTERVAL_SEC = 60
    MAXNUMBER_RUNNING_PROCESS = 1


class ProductionConfig(Config):
    DATABASE_URI = 'mysql://user@localhost/foo'


class DevelopmentConfig(Config):
    DEBUG = True
    CRON_INTERVAL_SEC = 1
    DATABASE_URI = 'sqlite:///'


class TestingConfig(Config):
    TESTING = True
