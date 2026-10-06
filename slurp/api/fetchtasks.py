from enum import Enum
from typing import Annotated, Any

from flask import current_app, request
from flask_restx import Namespace, Resource, abort, fields
from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    ValidationError,
    field_serializer,
)
from redis_om import model

from slurp.fetchers.types import Format
from slurp.models.task import Fetch, FetchEvent
from slurp.tasks import create_fetch, enqueue_fetch

api = Namespace("task", description="Fetch tasks")


class __EnumValue(fields.Raw):
    def format(self, value):
        return value.value


fetchMetadata = api.model(
    "FetchMetadata",
    {
        "name": fields.String(description="Name of the media"),
        "author": fields.String(description="Author of the media"),
        "author_url": fields.String(
            description="The URL where the author of this media can be found"
        ),
        "ts_upload": fields.DateTime(description="Time when the media was uploaded"),
        "duration": fields.Integer(description="Duration of the media in seconds"),
        "format": fields.String(
            description="Descriptive format of the format that the media will be downloaded in"
        ),
        "thumbnail_url": fields.String(description="Thumbnail url"),
    },
)

fetchEvent = api.model(
    "FetchEvent",
    {
        "fetch_id": fields.String(description="The ID to which this Event relates"),
        "ts_created": fields.DateTime(description="Created time"),
        "typ": fields.String(description="Event type"),
        "level": fields.String(description="Event level"),
        "message": fields.String(description="Event message"),
        "status": fields.Integer(description="Event status"),
    },
)

fetchTask = api.model(
    "FetchTask",
    {
        "id": fields.String(attribute="pk", description="ID of task"),
        "ts_created": fields.DateTime(description="Created time"),
        "ts_updated": fields.DateTime(description="Last updated time"),
        "url": fields.String(description="URL that task fetches"),
        "slug": fields.String(description="Slug to save fetch as"),
        "format": __EnumValue(description="Download format"),
        "target": fields.String(description="Filesystem target identifier"),
        "status": __EnumValue(description="Task status"),
        "meta": fields.Nested(fetchMetadata, default={}),
        "output_path": fields.String(
            description="Output path on filesystem - only present if the task succeeded"
        ),
        "pruned": fields.Boolean(
            description="Task was pruned (the output was scrubbed from disk)"
        ),
        "purged": fields.Boolean(
            description="Task was purged (logs have been removed)"
        ),
        "worker_id": fields.String(description="Work ID - use to query work status"),
    },
)

createTask = api.model(
    "CreateTask",
    {
        "url": fields.String(description="URL that should be fetched", required=True),
        "format": fields.String(
            description="Download format, by name",
            enum=list(Format.__members__),
            required=True,
        ),
        "slug": fields.String(description="Slug to save fetch as", required=True),
        "target": fields.String(
            description="Filesystem target identifier. This MUST be a valid destination as configured.",
            required=True,
        ),  # make this not required?
        "force": fields.Boolean(
            description="Ignore sanity checks when fetching", default=False
        ),
    },
)


def accept_enum_name(enum: type[Enum]) -> BeforeValidator:
    """ "
    Pydantic validator that validates against the name of the enum value, not the value itself.
    See https://github.com/pydantic/pydantic/discussions/2980#discussioncomment-15042101
    """

    def validator(value: Any) -> Any:
        if isinstance(value, str) and value in enum.__members__:
            return enum[value]
        else:
            return value

    return BeforeValidator(validator)


class CreateTaskSchema(BaseModel):
    url: str = Field(description="URL that should be fetched")
    format: Annotated[Format | None, accept_enum_name(Format)] = Field(
        description="Download format"
    )

    @field_serializer("format")
    def serialize_format(self, format: Format) -> str:
        return format.name

    slug: str = Field(description="Slug to save fetch as")
    target: str = Field(
        description="Filesystem target identifier. This MUST be a valid destination as configured."
    )
    force: bool = Field(default=False, description="Ignore sanity checks when fetching")


@api.route("/")
class List(Resource):
    @api.doc("list_tasks")
    @api.marshal_list_with(fetchTask)
    def get(self):
        fetches = (
            Fetch.find()
            .sort_by(
                "ts_created",
            )
            .all()
        )
        return fetches

    @api.doc("create_task")
    @api.expect(createTask)
    # @api.marshal_with(fetchTask)
    def post(self):
        try:
            # Handle JSON
            if request.is_json:
                raw_data = request.get_json()

            # Handle form-data / x-www-form-urlencoded
            else:
                raw_data = request.form.to_dict()

            # Validate with Pydantic
            try:
                data = CreateTaskSchema(**raw_data)
            except ValidationError as e:
                return {"message": "Validation failed", "errors": e.errors()}, 400

            # Safety: Validate the destination is permitted
            if data.target not in current_app.config["OUTPUTS"]:
                return {
                    "error": "This target is not valid. Please refer to Slurp's configuration."
                }, 400

            # Create the fetch - it is automatically worked on by the task queue.
            result = create_fetch.delay(
                url=data.url,
                fmt=data.format,
                target=data.target,
                slug=data.slug,
                force=data.force,
            )
            # Await the result from the worker.
            return {"fetch_id": result.get()}, 201
            # return {"message": "Task created", "data": data.model_dump()}, 200

        except ValidationError as e:
            return {"message": "Validation failed", "errors": e}, 400


@api.route("/<string:task_id>")
class Task(Resource):
    @api.doc("get_task")
    @api.marshal_with(fetchTask)
    def get(self, task_id):
        try:
            fetch = Fetch.get(task_id)
        except model.NotFoundError:
            return abort(404)
        return fetch


@api.route("/<string:task_id>/cancel")
class TaskCancel(Resource):
    @api.doc("cancel_task")
    @api.marshal_with(fetchTask)
    def post(self, task_id):
        """
        Cancel an existing task.
        Please note: this is best effort, and may leave the fetch in an unexpected state.
        """
        try:
            fetch = Fetch.get(task_id)
        except model.NotFoundError:
            return abort(404)

        try:
            fetch.abort()
        except AssertionError as e:
            return abort(400, str(e))
        return fetch


class RetryTaskSchema(BaseModel):
    force: bool = Field(
        default=False, description="Ignore sanity checks when retrying this task"
    )


retryTask = api.model(
    "RetryTask",
    {
        "force": fields.Boolean(
            description="Ignore sanity checks when retrying this task", default=False
        ),
    },
)


@api.route("/<string:task_id>/retry")
class TaskRetry(Resource):
    @api.doc("retry_task")
    @api.expect(retryTask)
    @api.marshal_with(fetchTask)
    def post(self, task_id):
        """
        Retry an existing task.
        The task must be in either the "success", "failed" or "cancelled" states.
        If "force" is set, the task's force option is updated before it is requeued.
        """
        # The body is optional - an empty request retries with the task's existing settings.
        if request.is_json:
            raw_data = request.get_json(silent=True) or {}
        else:
            raw_data = request.form.to_dict()

        try:
            data = RetryTaskSchema(**raw_data)
        except ValidationError as e:
            return {"message": "Validation failed", "errors": e.errors()}, 400

        try:
            fetch = Fetch.get(task_id)
        except model.NotFoundError:
            return abort(404)
        assert fetch.pk, "fetch does not have a primary key - this should never happen"

        if fetch.status not in (
            fetch.TaskStatus.success,
            fetch.TaskStatus.failed,
            fetch.TaskStatus.cancelled,
        ):
            return abort(400, "task not in retryable state")

        fetch.emit_event("log", "info", "Retrying fetch task")

        # Persist the new force value before requeuing, as enqueue_fetch reloads the fetch from the database.
        fetch.force = data.force
        fetch.save()

        try:
            worker_id = enqueue_fetch(fetch.pk)
        except AssertionError as e:
            return abort(400, str(e))
        fetch.worker_id = worker_id
        return fetch


@api.route("/<string:task_id>/events")
class TaskEvents(Resource):
    @api.doc("get_events")
    @api.marshal_list_with(fetchEvent)
    def get(self, task_id):
        events = (
            FetchEvent.find(FetchEvent.fetch_id == task_id).sort_by("ts_created").all()
        )
        return events


@api.route("/worker/<string:worker_id>")
class Work(Resource):
    @api.doc("get_task_by_worker")
    @api.marshal_with(fetchTask)
    def get(self, worker_id):
        fetch_obj = Fetch.find(worker_id == worker_id).first()
        return fetch_obj
