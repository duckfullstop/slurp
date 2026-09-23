from flask import current_app
from flask_restx import Namespace, Resource, fields

# Ordered must be set here otherwise lists don't have the desired output order, which is important for display purposes
api = Namespace("config", description="Application configuration", ordered=True)

fetcherInfo = api.model(
    "Fetcher Info",
    {
        "services": fields.List(
            fields.String,
            description="Services supported by this fetcher",
            example=["youtube", "x"],
        ),
    },
)

fetcherMap = api.model(
    "Fetchers",
    {
        "*": fields.Wildcard(
            fields.Nested(fetcherInfo),
            description="Fetcher name mapped to its info",
            example={"services": ["youtube", "x"]},
        ),
    },
)

outputsMap = api.model(
    "Outputs",
    {
        "*": fields.Wildcard(
            fields.String,
            description="Friendly name to refer to this output as",
            example="Vantage (normal pipeline)",
        ),
    },
)

configModel = api.model(
    "Config",
    {
        "fetchers": fields.Nested(
            fetcherMap,
            description="Available fetchers, keyed by name",
            example={"yt-dlp": {"services": ["youtube", "x"]}},
        ),
        "outputs": fields.Nested(
            outputsMap,
            description="Configured output target identifiers",
            example={"/data/ingest": "Vantage (normal pipeline)"},
        ),
        "purge": fields.Integer(
            description="Number of hours after which task logs are removed",
            example=48,
        ),
        "prune": fields.Integer(
            description="Number of hours after which task output files are removed",
            example=24,
        ),
    },
)


@api.route("/")
class Config(Resource):
    @api.doc("config")
    @api.marshal_with(configModel)
    def get(self):
        fetchers_formatted = {}
        for fetcher in current_app.extensions["fetchers"].get_all():
            fetchers_formatted[fetcher.name] = {"services": fetcher.service_names}
        return {
            "fetchers": fetchers_formatted,
            # This is a stub for eventual proper functionality in #92
            "outputs": {v: v for v in current_app.config["OUTPUTS"]},
            "purge": current_app.config["PURGE_AFTER"],
            "prune": current_app.config["PRUNE_AFTER"],
        }
