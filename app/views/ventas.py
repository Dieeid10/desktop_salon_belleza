import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date, timedelta

from app.views._base import DataView


class ComprobanteView(DataView):
    def __init__(self, master: tk.Misc, salon, *, email: str) -> None:
        super().__init__(master, salon)
        self.email = email
        self.selected_client: dict | None = None
        self.turns: list[dict] = []
        self.services: dict[int, str] = {}
        self.clients: dict[int, str] = {}

        controls = tk.Frame(self, pady=10)
        controls.pack(fill="x")
        self.client_label = ttk.Label(controls, text="Cliente: cualquiera")
        self.client_label.pack(side="left", padx=10)
        ttk.Label(controls, text="Turno realizado:").pack(side="left", padx=5)
        self.turn_list = tk.Listbox(controls, height=5, width=68, exportselection=0)
        self.turn_list.pack(side="left", padx=5)
        scrollbar = ttk.Scrollbar(controls, orient="vertical", command=self.turn_list.yview)
        scrollbar.pack(side="left", fill="y")
        self.turn_list.configure(yscrollcommand=scrollbar.set)
        self.turn_list.bind("<<ListboxSelect>>", self._update_button)
        actions = ttk.Frame(controls)
        actions.pack(side="left", padx=8, fill="y")
        ttk.Label(actions, text="Detalle del descuento por chisme:").pack(anchor="w")
        self.detail = ttk.Entry(actions, width=30)
        self.detail.pack(anchor="w", pady=4)
        self.generate_button = tk.Button(
            actions, text="Generar Ticket", bg="#aaaaaa", fg="#666666",
            state="disabled", command=lambda: self.run_action(self.register),
        )
        self.generate_button.pack(anchor="w", pady=8)
        tk.Button(
            actions, text="Actualizar Lista", bg="#5bc0de", fg="black",
            command=lambda: self.run_action(self.refresh),
        ).pack(anchor="w")

        self.ticket = tk.Text(self, font=("Courier", 10), bg="#FDF5E6", fg="black", wrap="none")
        self.ticket.pack(fill="both", expand=True, padx=20, pady=10)

    def refresh(self) -> None:
        today = date.today()
        self.turns = self.salon.listar_turnos(today - timedelta(days=3650), today)
        self.clients = {
            client["id"]: f"{client['nombre']} {client['apellido']}"
            for client in self.salon.listar_clientes_con_estado()
        }
        self.services = {
            service["id"]: service["nombre_servicio"]
            for service in self.salon.listar_servicios(gestion=True)
        }
        sold_turns = {
            sale.get("turno_id") for sale in self.salon.listar_ventas()
            if sale.get("turno_id") is not None
        }
        self.turns = [
            turn for turn in self.turns
            if turn["estado"].casefold() in {"completado", "realizado"}
            and turn["id"] not in sold_turns
        ]
        self._render_turns()

    def filter_client(self, client: dict | None) -> None:
        self.selected_client = client
        if client:
            self.client_label.configure(text=f"Cliente: {client['nombre']} {client['apellido']}")
        else:
            self.client_label.configure(text="Cliente: cualquiera")
        self._render_turns()

    def _render_turns(self) -> None:
        self.turn_list.delete(0, tk.END)
        for turn in self.turns:
            if self.selected_client and turn["cliente_id"] != self.selected_client["id"]:
                continue
            names = ", ".join(item["nombre"] for item in turn.get("detalles", []))
            client_name = self.clients.get(turn["cliente_id"], "Cliente")
            self.turn_list.insert(
                tk.END,
                f"#{turn['id']}  {turn['inicio']}  {client_name}  |  {names}  |  ${turn['total']}",
            )
        self._update_button()

    def _selected_turn(self) -> dict | None:
        selection = self.turn_list.curselection()
        if not selection:
            return None
        visible = [
            turn for turn in self.turns
            if not self.selected_client or turn["cliente_id"] == self.selected_client["id"]
        ]
        return visible[selection[0]]

    def _update_button(self, _event=None) -> None:
        enabled = self._selected_turn() is not None
        self.generate_button.configure(
            state="normal" if enabled else "disabled",
            bg="blue" if enabled else "#aaaaaa",
            fg="white" if enabled else "#666666",
        )

    def register(self) -> None:
        turn = self._selected_turn()
        if turn is None:
            raise ValueError("Seleccioná un turno realizado.")
        sale = self.salon.registrar_venta(turn["id"], self.detail.get().strip())
        details = []
        for detail in sale["detalles"]:
            name = self.services.get(detail["servicio_id"], f"Servicio {detail['servicio_id']}")
            details.append(f" {name:<25} ${detail['precio_cobrado']:>9}")
        ticket = (
            "\n=========================================\n"
            "          TICKET DE SERVICIO\n"
            "       - SALÓN DE BELLEZA GLAM -\n"
            "=========================================\n"
            f"Emitido por: {self.email}\n"
            f"Cliente: {self.clients.get(turn['cliente_id'], 'Cliente')} (ID: {turn['cliente_id']})\n"
            f"Turno: {turn['id']}\n"
            "-----------------------------------------\n"
            "Detalle:\n" + "\n".join(details) + "\n"
            "-----------------------------------------\n"
            f"SUBTOTAL:                         ${sale['subtotal']}\n"
            f"DESCUENTO:                        ${sale['descuento_chisme']}\n"
            f"TOTAL:                            ${sale['total']}\n"
            "=========================================\n"
            "  * Guardado en historial del sistema *\n"
            "=========================================\n"
        )
        self.ticket.delete("1.0", tk.END)
        self.ticket.insert(tk.END, ticket)
        self.detail.delete(0, tk.END)
        self.turns.remove(turn)
        self._render_turns()
        messagebox.showinfo("Venta Registrada", "El comprobante quedó guardado en el historial.", parent=self)


class HistorialView(DataView):
    def __init__(self, master: tk.Misc, salon) -> None:
        super().__init__(master, salon)
        toolbar = tk.Frame(self, padx=20, pady=10)
        toolbar.pack(fill="x")
        tk.Label(toolbar, text="Registro Histórico de Facturación", font=("Arial", 12, "bold")).pack(side="left")
        tk.Button(
            toolbar, text="Actualizar Lista", bg="#5bc0de", fg="black",
            command=lambda: self.run_action(self.refresh),
        ).pack(side="right")
        columns = ("ID Venta", "Fecha / Hora", "Cliente", "Servicio Realizado", "Monto Cobrado", "Atendido Por")
        self.table = self.tree(
            self, columns,
            {"ID Venta": 70, "Fecha / Hora": 145, "Cliente": 140,
             "Servicio Realizado": 200, "Monto Cobrado": 105, "Atendido Por": 115},
        )

    def refresh(self) -> None:
        sales = self.salon.listar_ventas()
        clients = {
            client["id"]: f"{client['nombre']} {client['apellido']}"
            for client in self.salon.listar_clientes_con_estado()
        }
        services = {
            service["id"]: service["nombre_servicio"]
            for service in self.salon.listar_servicios(gestion=True)
        }
        self.clear_tree(self.table)
        for sale in sales:
            names = ", ".join(
                services.get(detail["servicio_id"], "Servicio eliminado")
                for detail in sale["detalles"]
            )
            self.table.insert("", tk.END, values=(
                sale["id"], sale["fecha_hora"].replace("T", " ")[:16],
                clients.get(sale.get("cliente_id"), "Cliente eliminado"), names,
                f"${sale['total']}", str(sale.get("empleado_id") or "N/A")[:12],
            ))

    def refresh(self) -> None:
        sales = self.salon.listar_ventas()
        self.clear_tree(self.table)
        for sale in sales:
            self.table.insert("", "end", values=(
                sale["id"], sale["fecha_hora"], sale.get("cliente_id") or "",
                sale.get("turno_id") or "", sale["subtotal"], sale["descuento_chisme"],
                sale["total"], sale.get("chisme_detalle") or "",
            ))

    def register(self) -> None:
        turn_id = int(self.turn_id.get().strip())
        sale = self.salon.registrar_venta(turn_id, self.detail.get().strip())
        self.turn_id.set("")
        self.detail.set("")
        self.refresh()
        messagebox.showinfo(
            "Venta registrada",
            f"Comprobante #{sale['id']}\nTotal: ${sale['total']}",
            parent=self,
        )