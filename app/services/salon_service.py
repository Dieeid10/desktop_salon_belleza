from datetime import date
from typing import Any

from app.services.api_client import ApiClient, ApiError


class SalonService:
    def __init__(self, api: ApiClient) -> None:
        self.api = api

    @staticmethod
    def _client_to_desktop(client: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": client["id"],
            "nombre": client["first_name"],
            "apellido": client["last_name"],
            "telefono": client.get("phone"),
            "email": client.get("email"),
            "activo": client["is_active"],
            "fecha_creacion": client["created_at"],
        }

    @staticmethod
    def _service_to_desktop(service: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": service["id"],
            "nombre_servicio": service["name"],
            "descripcion": service.get("description"),
            "precio": service["price"],
            "duracion_minutos": service["duration_minutes"],
            "visible_online": service["visible_online"],
            "activo": service["is_active"],
        }

    @staticmethod
    def _appointment_to_desktop(appointment: dict[str, Any]) -> dict[str, Any]:
        states = {
            "pending": "pendiente",
            "confirmed": "confirmado",
            "completed": "completado",
            "cancelled": "cancelado",
            "absent": "ausente",
        }
        return {
            "id": appointment["id"],
            "cliente_id": appointment.get("client_id"),
            "profesional_id": appointment["professional_id"],
            "inicio": appointment["starts_at"],
            "fin": appointment["ends_at"],
            "estado": states.get(appointment["status"], appointment["status"]),
            "total": appointment["total"],
            "detalles": [
                {
                    "servicio_id": detail["service_id"],
                    "nombre": detail["name"],
                    "duracion_min": detail["duration_minutes"],
                    "precio": detail["price"],
                }
                for detail in appointment.get("details", [])
            ],
        }

    @staticmethod
    def _sale_to_desktop(sale: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": sale["id"],
            "fecha_hora": sale["date_time"],
            "cliente_id": sale.get("client_id"),
            "empleado_id": sale.get("employee_id"),
            "turno_id": sale.get("appointment_id"),
            "descuento_chisme_id": sale.get("gossip_discount_id"),
            "chisme_pct": sale["gossip_percentage"],
            "chisme_detalle": sale.get("gossip_details"),
            "subtotal": sale["subtotal"],
            "descuento_chisme": sale["gossip_discount"],
            "total": sale["total"],
            "detalles": [
                {
                    "servicio_id": detail.get("service_id"),
                    "descuento_id": detail.get("discount_id"),
                    "precio_lista": detail.get("list_price"),
                    "descuento_pct": detail["service_discount_percentage"],
                    "precio_cobrado": detail["charged_price"],
                }
                for detail in sale.get("details", [])
            ],
        }

    def listar_clientes(self) -> list[dict[str, Any]]:
        clients = self.api.request("GET", "/clients/")
        return [self._client_to_desktop(client) for client in clients]

    def listar_clientes_con_estado(self) -> list[dict[str, Any]]:
        clients = self.api.request(
            "GET", "/clients/", params={"only_active": "false"}
        )
        return [self._client_to_desktop(client) for client in clients]

    def crear_cliente(self, datos: dict[str, Any]) -> dict[str, Any]:
        client = self.api.request(
            "POST",
            "/clients/",
            json={
                "first_name": datos["nombre"],
                "last_name": datos["apellido"],
                "phone": datos.get("telefono"),
                "email": datos.get("email"),
            },
        )
        return self._client_to_desktop(client)

    def actualizar_cliente(self, cliente_id: int, datos: dict[str, Any]) -> dict[str, Any]:
        client = self.api.request(
            "PUT",
            f"/clients/{cliente_id}",
            json={
                "first_name": datos["nombre"],
                "last_name": datos["apellido"],
                "phone": datos.get("telefono"),
                "email": datos.get("email"),
            },
        )
        return self._client_to_desktop(client)

    def activar_cliente(self, cliente_id: int) -> None:
        self.api.request("PATCH", f"/clients/{cliente_id}/activate")

    def desactivar_cliente(self, cliente_id: int) -> None:
        self.api.request("DELETE", f"/clients/{cliente_id}")

    def listar_servicios(self, gestion: bool = False) -> list[dict[str, Any]]:
        path = "/services/management" if gestion else "/services/"
        services = self.api.request("GET", path)
        return [self._service_to_desktop(service) for service in services]

    def crear_servicio(self, datos: dict[str, Any]) -> dict[str, Any]:
        service = self.api.request(
            "POST",
            "/services/",
            json={
                "name": datos["nombre_servicio"],
                "description": datos.get("descripcion"),
                "price": datos["precio"],
                "duration_minutes": datos["duracion_minutos"],
                "visible_online": datos.get("visible_online", True),
            },
        )
        return self._service_to_desktop(service)

    def actualizar_servicio(self, servicio_id: int, datos: dict[str, Any]) -> dict[str, Any]:
        service = self.api.request(
            "PUT",
            f"/services/{servicio_id}",
            json={
                "name": datos["nombre_servicio"],
                "description": datos.get("descripcion"),
                "price": datos["precio"],
                "duration_minutes": datos["duracion_minutos"],
                "visible_online": datos.get("visible_online", True),
            },
        )
        return self._service_to_desktop(service)

    def desactivar_servicio(self, servicio_id: int) -> None:
        self.api.request("DELETE", f"/services/{servicio_id}")

    def listar_profesionales(self) -> list[dict[str, Any]]:
        professionals = self.api.request("GET", "/professionals/")
        return [
            {
                "id": person["id"],
                "nombre": person["name"],
                "perfil_id": person.get("profile_id"),
                "activo": person["is_active"],
            }
            for person in professionals
        ]

    def es_duena(self) -> bool:
        try:
            self.api.request("GET", "/discounts/management")
            return True
        except ApiError as error:
            if error.status_code == 403:
                return False
            raise

    def listar_descuentos(self, gestion: bool = False) -> list[dict[str, Any]]:
        path = "/discounts/management" if gestion else "/discounts/"
        discounts = self.api.request("GET", path)
        return [
            {
                "id": discount["id"],
                "nombre": discount["name"],
                "tipo": "servicio" if discount["type"] == "service" else "chisme",
                "porcentaje": discount["percentage"],
                "servicio_id": discount.get("service_id"),
                "fecha_inicio": discount.get("start_date"),
                "fecha_fin": discount.get("end_date"),
                "activo": discount["is_active"],
            }
            for discount in discounts
        ]

    def listar_turnos(
        self,
        desde: date,
        hasta: date,
        *,
        profesional_id: int | None = None,
        estado: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "start_date": desde.isoformat(),
            "end_date": hasta.isoformat(),
        }
        if profesional_id is not None:
            params["professional_id"] = profesional_id
        if estado:
            params["status"] = self._status_to_mvc(estado)
        appointments = self.api.request(
            "GET",
            "/admin/appointments/",
            params=params,
        )
        return [self._appointment_to_desktop(item) for item in appointments]

    def consultar_disponibilidad(
        self, profesional_id: int, fecha: date, servicio_ids: list[int]
    ) -> dict[str, Any]:
        params: list[tuple[str, Any]] = [
            ("professional_id", profesional_id), ("day", fecha.isoformat())
        ]
        params.extend(("service_ids", servicio_id) for servicio_id in servicio_ids)
        result = self.api.request(
            "GET", "/appointments/availability", params=params
        )
        return {
            "profesional_id": result["professional_id"],
            "fecha": result["date"],
            "duracion_min": result["duration_minutes"],
            "horarios": result["available_starts"],
        }

    def reservar_turno(self, datos: dict[str, Any]) -> dict[str, Any]:
        appointment = self.api.request(
            "POST",
            "/appointments/",
            json={
                "first_name": datos["nombre"],
                "last_name": datos["apellido"],
                "phone": datos["telefono"],
                "professional_id": datos["profesional_id"],
                "service_ids": datos["servicio_ids"],
                "starts_at": datos["inicio"],
            },
        )
        return self._appointment_to_desktop(appointment)

    def cambiar_estado_turno(self, turno_id: int, estado: str) -> dict[str, Any]:
        mvc_status = self._status_to_mvc(estado)
        if mvc_status == "cancelled":
            appointment = self.api.request(
                "POST", f"/admin/appointments/{turno_id}/cancel"
            )
        else:
            appointment = self.api.request(
                "PATCH",
                f"/admin/appointments/{turno_id}/status",
                json={"new_status": mvc_status},
            )
        return self._appointment_to_desktop(appointment)

    def listar_ventas(self) -> list[dict[str, Any]]:
        sales = self.api.request("GET", "/sales/")
        return [self._sale_to_desktop(sale) for sale in sales]

    def registrar_venta(self, turno_id: int, detalle: str | None = None) -> dict[str, Any]:
        sale = self.api.request(
            "POST",
            "/sales/",
            json={"appointment_id": turno_id, "gossip_details": detalle or None},
        )
        return self._sale_to_desktop(sale)

    @staticmethod
    def _status_to_mvc(status: str) -> str:
        return {
            "pendiente": "pending",
            "confirmado": "confirmed",
            "completado": "completed",
            "cancelado": "cancelled",
            "ausente": "absent",
        }.get(status.casefold(), status.casefold())