from celery import Task
from celery.contrib.abortable import AbortableTask
from flask import Flask


class FlaskTask(Task):
    """Celery task base that runs every task inside the Flask app context."""

    flask_app: Flask

    def __call__(self, *args: object, **kwargs: object) -> object:
        with self.flask_app.app_context():
            return self.run(*args, **kwargs)


class AbortableFlaskTask(AbortableTask, FlaskTask):
    """
    Abortable task that also runs inside the Flask app context.
    Passing base=AbortableTask alone would replace the app's task_cls and drop the context.
    """
