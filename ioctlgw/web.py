from flask import Flask
from flask_restx import Api, Resource
from ioctlgw import __VERSION__

import threading


class WebService(threading.Thread):

    app = Flask(__name__)
    api = Api(app, title=f"IO Controller Gateway v{__VERSION__}", description="Multi protocol IO controller gateway", contact="https://github.com/natm/iocontroller-gateway", contact_url="https://github.com/natm/iocontroller-gateway")

    def __init__(self, controllers):
        threading.Thread.__init__(self)
        self.controllers = controllers

    def run(self):
        self.app.run(port=8080)

    @api.route('/controllers/')
    class Controllers(Resource):
        def get(self):
            return self.controllers.keys()

    @api.route('/controllers/<string:name>/')
    class Controller(Resource):
        def get(self):
            return {'hello': 'world'}

    @api.route('/controllers/<string:name>/relays/')
    class Controller(Resource):
        def get(self):
            return {'hello': 'world'}

    @api.route('/controllers/<string:name>/digital_inputs/')
    class Controller(Resource):
        def get(self):
            return {'hello': 'world'}

