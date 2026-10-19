from typing import Any

import httpx

from app.session import Session


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


class ApiClient:
    def __init__(self, base_url: str, session: Session) -> None:
        self.base_url = base_url
        self.session = session
        self.http = httpx.Client(base_url=base_url, timeout=10.0)

    def close(self) -> None:
        self.http.close()

    def request(self, method: str, path: str, *, authenticated: bool = True, retry_auth: bool = True, **kwargs: Any ) -> Any:
        headers = dict(kwargs.pop("headers", {}))
        if authenticated and self.session.access_token:
            headers["Authorization"] = f"Bearer {self.session.access_token}"

        try:
            response = self.http.request(method, path, headers=headers, **kwargs)
        except httpx.RequestError as error:
            raise ApiError(f"No se pudo conectar con la API ({self.base_url}).") from error

        if response.status_code == 401 and authenticated and retry_auth:
            self._refresh_session()
            return self.request(
                method,
                path,
                authenticated=True,
                retry_auth=False,
                **kwargs,
            )

        if not response.is_success:
            detail = self._error_detail(response)
            raise ApiError(detail, response.status_code)
        if response.status_code == 204:
            return None
        return response.json()

    def _refresh_session(self) -> None:
        refresh_token = self.session.refresh_token
        if not refresh_token:
            self.session.clear()
            raise ApiError("La sesión venció. Iniciá sesión nuevamente.")
        try:
            response = self.http.post(
                "/auth/refresh",
                json={"refresh_token": refresh_token},
            )
        except httpx.RequestError as error:
            raise ApiError("No se pudo renovar la sesión.") from error
        if not response.is_success:
            self.session.clear()
            raise ApiError("La sesión venció. Iniciá sesión nuevamente.")
        self.session.update(response.json())

    @staticmethod
    def _error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return f"La API respondió con HTTP {response.status_code}."
        detail = payload.get("detail", "")
        if isinstance(detail, list):
            return "; ".join(str(item.get("msg", item)) for item in detail)
        return str(detail or f"La API respondió con HTTP {response.status_code}.")