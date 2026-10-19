from datetime import date
from typing import Any

from app.services.api_client import ApiClient, ApiError


class SalonService:
    def __init__(self, api: ApiClient) -> None:
        self.api = api

    def listar_clientes(self) -> list[dict[str, Any]]:
        return self.api.request("GET", "/clientes/")

    def listar_clientes_con_estado(self) -> list[dict[str, Any]]:
        return self.api.request(
            "GET", "/clientes/", params={"solo_activos": "false"}
        )

    def crear_cliente(self, datos: dict[str, Any]) -> dict[str, Any]:
        return self.api.request("POST", "/clientes/", json=datos)

    def actualizar_cliente(self, cliente_id: int, datos: dict[str, Any]) -> dict[str, Any]:
        return self.api.request("PUT", f"/clientes/{cliente_id}", json=datos)

    def activar_cliente(self, cliente_id: int) -> None:
            self.api.request("PATCH", f"/clientes/{cliente_id}/activar")

    def desactivar_cliente(self, cliente_id: int) -> None:
        self.api.request("DELETE", f"/clientes/{cliente_id}")

    def listar_servicios(self, gestion: bool = False) -> list[dict[str, Any]]:
        path = "/servicios/gestion" if gestion else "/servicios/"
        return self.api.request("GET", path)

    def crear_servicio(self, datos: dict[str, Any]) -> dict[str, Any]:
        return self.api.request("POST", "/servicios/", json=datos)

    def actualizar_servicio(self, servicio_id: int, datos: dict[str, Any]) -> dict[str, Any]:
        return self.api.request("PUT", f"/servicios/{servicio_id}", json=datos)

    def desactivar_servicio(self, servicio_id: int) -> None:
        self.api.request("DELETE", f"/servicios/{servicio_id}")

    def listar_profesionales(self) -> list[dict[str, Any]]:
        return self.api.request("GET", "/profesionales/")

    def es_duena(self) -> bool:
        try:
            self.api.request("GET", "/descuentos/gestion")
            return True
        except ApiError as error:
            if error.status_code == 403:
                return False
            raise

    def listar_descuentos(self, gestion: bool = False) -> list[dict[str, Any]]:
        path = "/descuentos/gestion" if gestion else "/descuentos/"
        return self.api.request("GET", path)

    def listar_turnos(
        self,
        desde: date,
        hasta: date,
        *,
        profesional_id: int | None = None,
        estado: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "desde": desde.isoformat(),
            "hasta": hasta.isoformat(),
        }
        if profesional_id is not None:
            params["profesional_id"] = profesional_id
        if estado:
            params["estado"] = estado
        return self.api.request(
            "GET",
            "/admin/turnos/",
            params=params,
        )

    def consultar_disponibilidad(
        self, profesional_id: int, fecha: date, servicio_ids: list[int]
    ) -> dict[str, Any]:
        params: list[tuple[str, Any]] = [
            ("profesional_id", profesional_id), ("fecha", fecha.isoformat())
        ]
        params.extend(("servicio_ids", servicio_id) for servicio_id in servicio_ids)
        return self.api.request("GET", "/turnos/disponibilidad", params=params)

    def reservar_turno(self, datos: dict[str, Any]) -> dict[str, Any]:
        return self.api.request("POST", "/turnos/", json=datos)

    def cambiar_estado_turno(self, turno_id: int, estado: str) -> dict[str, Any]:
        return self.api.request(
            "PATCH",
            f"/admin/turnos/{turno_id}/estado",
            json={"nuevo_estado": estado},
        )

    def listar_ventas(self) -> list[dict[str, Any]]:
        return self.api.request("GET", "/ventas/")

    def registrar_venta(self, turno_id: int, detalle: str | None = None) -> dict[str, Any]:
        return self.api.request(
            "POST",
            "/ventas/",
            json={"turno_id": turno_id, "chisme_detalle": detalle or None},
        )