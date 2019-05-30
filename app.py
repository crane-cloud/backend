import os

from flask import Flask

# import config options
from config import app_config

# get the running config
config_name = os.getenv('FLASK_APP_CONFIG')

app = Flask(__name__)

# use running config settings on app
app.config.from_object(app_config[config_name])

@app.route('/')
def hello():
    return 'hello world'

if __name__ == '__main__':
    app.run()