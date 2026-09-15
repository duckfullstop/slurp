from flask import (
    Blueprint,
    render_template,
)

main_blueprint = Blueprint("main", __name__)


@main_blueprint.route("/", defaults={"path": ""})
@main_blueprint.route("/<path:path>")
def catch_all(path):
    return render_template("index.html")
