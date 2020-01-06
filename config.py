import os

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False
DEBUG = True
APNS_CERTIFICATE = 'test.pem'
APNS_SANDBOX = False
GCM_API_KEY = '<some_key>'
JOBS = [
        {
            'id': 'first',
            'func': 'app.api:first_routes',
            'trigger': 'interval',
            'seconds': 120
        }, {
            'id': 'second',
            'func': 'app.api:second_routes',
            'trigger': 'interval',
            'seconds': 300
        }, {
            'id': 'third',
            'func': 'app.api:third_routes',
            'trigger': 'interval',
            'seconds': 1860
        }
    ]	
