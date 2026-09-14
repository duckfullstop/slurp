import json
from datetime import UTC, datetime

from redis_om import Field, JsonModel

from slurp import db


class BaseModel(JsonModel):
    """
    Base model
    """

    ts_created: datetime = Field(
        sortable=True,
        default_factory=datetime.now(UTC).now,
    )
    ts_updated: datetime = Field(sortable=True, default=datetime.now(UTC))

    def save(self, **kwargs):
        self.ts_updated = datetime.now(UTC)
        super().save(**kwargs)

    class Meta:
        database = db.redis

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
