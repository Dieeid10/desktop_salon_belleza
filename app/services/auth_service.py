from app.services.api_client import ApiClient
from app.session import Session


class AuthService:
    def __init__(self, api: ApiClient, session: Session) -> None:
        self.api = api
        self.session = session

    def login(self, email: str, password: str) -> None:
        tokens = self.api.request(
            "POST",
            "/auth/login",
            authenticated=False,
            json={"email": email, "password": password},
        )
        self.session.update(tokens)

    def logout(self) -> None:
        self.session.clear()