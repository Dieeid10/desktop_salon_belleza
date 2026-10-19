# Desktop

Cliente Tkinter de la API del salón. No conecta directamente a PostgreSQL ni
guarda credenciales en archivos. El access token y el refresh token viven en
memoria mientras la aplicación está abierta.

Desde esta carpeta, con `.myvenv` ya activado:

```sh
uv sync --active
SALON_API_URL=http://127.0.0.1:8000 uv run --active main.py
```

En Linux o macOS, activá el entorno con `source .myvenv/bin/activate`. En
Windows, activalo con `.myvenv\\Scripts\\Activate.ps1` y ejecutá
`uv sync --active` y `uv run --active main.py`. `SALON_API_URL` es opcional y
por defecto apunta a `http://127.0.0.1:8000`.

La sesión se renueva contra `/auth/refresh` cuando la API responde `401`.
Cerrar sesión o cerrar la ventana descarta ambos tokens. La gestión de usuarios
no está incluida porque la API todavía no publica endpoints para crear usuarios
ni cambiar contraseñas.

duena@gmail.com
NuevaClave123