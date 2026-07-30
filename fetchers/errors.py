# shared exception type for all fetchers


class FetchError(Exception):
    def __init__(self, message: str, source: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.source = source

    def __str__(self) -> str:
        if self.source:
            return f"[{self.source}] {self.message}"
        return self.message
