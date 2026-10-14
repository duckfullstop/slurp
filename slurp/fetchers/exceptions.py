class FetcherMisconfiguredError(Exception):
    pass


class NoUpstreamMetadataError(Exception):
    pass


class AmbiguousQueryError(Exception):
    pass


class PlaylistDetected(Exception):
    """Raised by a fetcher when the requested URL is a playlist rather than a single piece of media."""

    def __init__(self, entries):
        super().__init__(f"URL is a playlist of {len(entries)} entries")
        self.entries = entries


class PlaylistExpanded(Exception):
    """Raised by the fetch task once a playlist has been replaced by a Fetch per entry. Carries the new Fetches' PKs."""

    def __init__(self, pks: list[str]):
        super().__init__(f"Playlist expanded into {len(pks)} fetches")
        self.pks = pks


class NoFetchersAvailable(Exception):
    def __str__(self):
        return "No configured fetchers are available"


class FetchersExhaustedError(Exception):
    def __str__(self):
        return "Available Fetchers exhausted"


class FetchLockedError(Exception):
    def __str__(self):
        return "Fetch locked by another worker"


class FetchAbortedError(Exception):
    def __str__(self):
        return "Fetch aborted on request"
