import tkinter as tk
from tkinter import messagebox

from app.config import API_URL
from app.services.api_client import ApiClient, ApiError
from app.services.auth_service import AuthService
from app.services.salon_service import SalonService
from app.session import Session
from app.views.dashboard import DashboardView
from app.views.login import LoginView


class DesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Salón | Gestión")
        self.root.geometry("300x220")
        self.root.resizable(True, True)

        self.session = Session()
        self.api = ApiClient(API_URL, self.session)
        self.auth = AuthService(self.api, self.session)
        self.salon = SalonService(self.api)
        self.is_owner = False
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.show_login()

    def show_login(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()
        self.root.title("Salón | Iniciar sesión")
        LoginView(self.root, self.login).pack(fill="both", expand=True)

    def login(self, email: str, password: str) -> None:
        try:
            self.auth.login(email, password)
        except ApiError as error:
            messagebox.showerror("No se pudo iniciar sesión", str(error), parent=self.root)
            return
        try:
            self.is_owner = self.salon.es_duena()
        except ApiError as error:
            self.is_owner = False
            messagebox.showwarning(
                "Permisos",
                f"La sesión inició, pero no se pudo consultar el rol. Se abrirá en modo restringido.\n{error}",
                parent=self.root,
            )
        self.show_dashboard(email)

    def show_dashboard(self, email: str) -> None:
        for child in self.root.winfo_children():
            child.destroy()
        self.root.title("Salón | Gestión")
        self.root.geometry("850x600")
        self.root.minsize(800, 550)
        DashboardView(
            self.root,
            email=email,
            is_owner=self.is_owner,
            salon=self.salon,
            on_logout=self.logout,
        ).pack(fill="both", expand=True)

    def logout(self) -> None:
        self.auth.logout()
        self.show_login()

    def close(self) -> None:
        self.auth.logout()
        self.api.close()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    DesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()