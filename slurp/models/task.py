import datetime
import enum

from celery.contrib.abortable import AbortableAsyncResult
from flask_sse import sse
from redis_om import Field

from slurp.fetchers.types import Format
from slurp.models.base import BaseModel


class FetchMetadata(BaseModel):
    """
    FetchMetadata describes information about a piece of media.
    """

    # Name of the media
    name: str | None = None
    # Author of the media
    author: str | None = None
    # Time when the media was uploaded
    ts_upload: datetime.datetime | None = None
    # Duration of the media in seconds - if fractional, round up
    duration: int | None = None
    # Desriptive format that the media will be downloaded in
    format: str | None = None
    # URL where the thumbnail can be retrieved
    thumbnail_url: str | None = None

    class Meta:
        embedded = True


class Fetch(BaseModel, index=True):
    """
    Fetch describes a task to grab a piece of media from the specified target.
    """

    url: str = Field(index=True)
    slug: str = Field(index=True)
    target: str | None = None
    format: Format = Format.VIDEO_AUDIO

    class TaskStatus(str, enum.Enum):
        # "created" tasks are awaiting processing or assignment to a worker.
        created = "created"
        # "Running" tasks are in the process of being fetched.
        running = "running"
        # "Aborting" tasks are in the process of being terminated mid-fetch.
        aborting = "aborting"
        # "Success" tasks completed their fetch successfully.
        success = "success"
        # "Failed" tasks failed to process for some reason.
        failed = "failed"
        # "Aborted" tasks were stopped midway, and are in an unknown state.
        cancelled = "aborted"
        # "Completed" tasks is one where it finished executing, but we don't know the outcome for some reason.
        completed = "completed"
        # "Unknown" tasks are ones where the execution state is a mystery to us.
        unknown = "unknown"

    status: TaskStatus = TaskStatus.unknown

    meta: FetchMetadata | None = None

    # The ID of the celery task.
    worker_id: str | None = Field(index=True, default=None)

    # The path to the output file - only set if the fetch succeeded.
    # If pruned is set, this path most likely does not exist, and is for information only.
    output_path: str | None = None

    # Whether this fetch has had its output data removed from the filesystem.
    pruned: bool = Field(index=True, default=False)

    # Whether this fetch has had its logs and events destroyed.
    purged: bool = Field(index=True, default=False)

    def lock(self, *args, **kwargs):
        return self.db().lock(name=self.pk, *args, **kwargs)

    def emit_event(self, typ: str, level: str, message: str, status: int = 0):
        db_log = FetchEvent(
            fetch_id=self.pk,
            typ=typ,
            level=level,
            message=message,
            status=status,
        )
        db_log.save()
        sse.publish(db_log.model_dump_json())

    def abort(self) -> None:
        """
        Attempt to cancel this Fetch if assigned to a worker.
        :return: nothing
        :raises: AssertionError
        """
        assert self.worker_id is not None, "worker not assigned to this Fetch"
        assert self.status in (
            self.TaskStatus.created,
            self.TaskStatus.running,
        ), "this task is not in an abortable state"

        # The worker polls this flag. It lives outside the model so that the worker's own whole-model
        # saves can't clobber it, and has an expiry so it can't outlive a task that never picks it up.
        self.db().set(self._abort_key, 1, ex=60 * 60 * 24)

        self.status = self.TaskStatus.aborting
        self.save()

        self.emit_event("abort_requested", "warning", "Abort requested")

        AbortableAsyncResult(str(self.worker_id)).abort()

    @property
    def _abort_key(self) -> str:
        return f"slurp:fetch:{self.pk}:abort"

    def abort_requested(self) -> bool:
        """
        Whether an abort has been requested for this Fetch. Safe to call from the worker.
        """
        return bool(self.db().exists(self._abort_key))


class FetchEvent(BaseModel, index=True):
    """
    FetchEvent is a given event related to a Fetch. These should be read in chronological order.
    """

    # The ID of the Fetch.
    fetch_id: str = Field(index=True)
    # The type of event.
    typ: str
    # The level of severity.
    level: str
    # The human-readable message.
    message: str
    # An optional status code.
    status: int = 0
