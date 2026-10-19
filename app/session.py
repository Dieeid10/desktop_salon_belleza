from dataclasses import dataclass


@dataclass
class Session:
    access_token: str | None = None
    refresh_token: str | None = None

    @property
    def authenticated(self) -> bool:
        return self.access_token is not None

    def update(self, tokens: dict) -> None:
        self.access_token = tokens["access_token"]
        self.refresh_token = tokens["refresh_token"]

    def clear(self) -> None:
        self.access_token = None
        self.refresh_token = None