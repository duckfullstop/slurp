from flask import current_app
from flask_restx import Namespace, Resource

api = Namespace("config", description="Application configuration")


@api.route("/")
class Config(Resource):
    @api.doc("config")
    def get(self):
        fetchers_formatted = {}
        for fetcher in current_app.extensions["fetchers"].get_all():
            fetchers_formatted[fetcher.name] = {"services": fetcher.service_names}
        return {
            "fetchers": fetchers_formatted,
            "outputs": current_app.config["OUTPUTS"],
        }
