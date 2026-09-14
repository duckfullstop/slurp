from flask import current_app
from flask_restx import Namespace, Resource

api = Namespace("config", description="Application configuration")


@api.route("/")
class Config(Resource):
    @api.doc("config")
    def get(self):
        return {"outputs": current_app.config["OUTPUTS"]}
