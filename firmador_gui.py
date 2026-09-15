import logging
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from dotenv import dotenv_values

from src.batch import list_pdfs, sign_batch
from src.config import app_dir, build_config

logging.getLogger("pyhanko").setLevel(logging.CRITICAL)

# Mismos valores que config.env.example, para precargar el formulario la
# primera vez que se abre (sin config.env previo).
DEFAULTS = {
    "IN_DIR": "./in",
    "OUT_DIR": "./out",
    "PFX_PATH": "./certs/tu-certificado.pfx",
    "PFX_PASSWORD": "",
    "SIGN_PAGE": "last",
    "POS_X": "326",
    "POS_Y": "350",
    "STAMP_WIDTH": "180",
    "STAMP_HEIGHT": "44",
    "IMAGE_PATH": "./assets/firma-template.png",
    "SIGNER_FIRST_NAME": "Nombre1 Nombre2",
    "SIGNER_LAST_NAME": "Apellido1 Apellido2",
    "NAME_FONT_SIZE": "34",
    "NAME_POS_X": "384",
    "NAME_POS_Y": "46",
    "DATE_FORMAT": "%Y-%m-%d %H:%M:%S",
    "DATE_FONT_SIZE": "24",
    "DATE_POS_X": "384",
    "DATE_POS_Y": "140",
    "FONT_PATH": "",
    "TEXT_COLOR": "0,0,0",
    "SIGN_REASON": "Firma electrónica avanzada",
    "SIGN_LOCATION": "Nombre Institución",
    "SIGN_CONTACT_INFO": "http://www.sitio-web-institucion.cl",
}

CERT_FILETYPES = [("Certificados", "*.pfx *.p12"), ("Todos los archivos", "*.*")]
IMAGE_FILETYPES = [("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Todos los archivos", "*.*")]
FONT_FILETYPES = [("Fuentes", "*.ttf *.otf"), ("Todos los archivos", "*.*")]


def config_env_path() -> Path:
    return app_dir() / "config.env"


def load_saved_values() -> tuple:
    path = config_env_path()
    if not path.is_file():
        return dict(DEFAULTS), True, ""

    raw = dotenv_values(path)
    values = dict(DEFAULTS)
    for key in DEFAULTS:
        if raw.get(key):
            values[key] = raw[key]

    sign_page_raw = (raw.get("SIGN_PAGE") or "last").strip()
    last_page = sign_page_raw.lower() == "last"
    page_number = "" if last_page else sign_page_raw
    return values, last_page, page_number


def write_config_env(values: dict, remember_password: bool) -> None:
    lines = []
    for key, value in values.items():
        if key == "PFX_PASSWORD" and not remember_password:
            value = ""
        lines.append(f"{key}={value}")
    config_env_path().write_text("\n".join(lines) + "\n", encoding="utf-8")


class FirmadorGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Firmador en masa")
        self.root.resizable(False, False)

        self.vars = {key: tk.StringVar(value=value) for key, value in DEFAULTS.items()}
        self.remember_var = tk.BooleanVar(value=False)
        self.last_page_var = tk.BooleanVar(value=True)
        self.page_number_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="")
        self.queue: "queue.Queue" = queue.Queue()
        self.running = False

        values, last_page, page_number = load_saved_values()
        for key, value in values.items():
            self.vars[key].set(value)
        self.last_page_var.set(last_page)
        self.page_number_var.set(page_number)

        self._build_ui()

    # --- construcción de la ventana ---

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        container = ttk.Frame(self.root, padding=12)
        container.grid(row=0, column=0, sticky="nsew")

        columns = ttk.Frame(container)
        columns.grid(row=0, column=0, columnspan=2, sticky="nsew")

        left = ttk.LabelFrame(columns, text="Carpetas y certificado", padding=10)
        left.grid(row=0, column=0, sticky="n", padx=(0, 8))
        right = ttk.LabelFrame(columns, text="Sello y firmante", padding=10)
        right.grid(row=0, column=1, sticky="n")

        row = 0
        for key, label in [("IN_DIR", "Entrada (IN_DIR)"), ("OUT_DIR", "Salida (OUT_DIR)")]:
            self._add_entry(left, row, label, key, browse="dir")
            row += 1

        ttk.Separator(left).grid(row=row, column=0, columnspan=3, sticky="ew", pady=6)
        row += 1

        self._add_entry(left, row, "Archivo .pfx", "PFX_PATH", browse=CERT_FILETYPES)
        row += 1
        self._add_entry(left, row, "Clave del PFX", "PFX_PASSWORD", show="*")
        row += 1
        ttk.Checkbutton(
            left,
            text="Recordar la clave en este equipo (menos seguro)",
            variable=self.remember_var,
        ).grid(row=row, column=0, columnspan=2, sticky="w", **pad)
        row += 1

        ttk.Separator(left).grid(row=row, column=0, columnspan=3, sticky="ew", pady=6)
        row += 1

        for key, label in [
            ("SIGN_REASON", "Motivo"),
            ("SIGN_LOCATION", "Lugar / Institución"),
            ("SIGN_CONTACT_INFO", "Contacto"),
        ]:
            self._add_entry(left, row, label, key)
            row += 1

        row = 0
        self._add_entry(right, row, "Imagen de fondo", "IMAGE_PATH", browse=IMAGE_FILETYPES)
        row += 1

        sizes = ttk.Frame(right)
        sizes.grid(row=row, column=0, columnspan=2, sticky="w", **pad)
        for i, (key, label) in enumerate([
            ("STAMP_WIDTH", "Ancho (pt)"),
            ("STAMP_HEIGHT", "Alto (pt)"),
            ("POS_X", "Pos. X"),
            ("POS_Y", "Pos. Y"),
        ]):
            ttk.Label(sizes, text=label).grid(row=0, column=i, padx=3, sticky="w")
            ttk.Entry(sizes, textvariable=self.vars[key], width=7).grid(row=1, column=i, padx=3)
        row += 1

        page_frame = ttk.Frame(right)
        page_frame.grid(row=row, column=0, columnspan=2, sticky="w", **pad)
        ttk.Label(page_frame, text="Página a firmar:").grid(row=0, column=0)
        validate_page = (self.root.register(self._validate_page_input), "%P")
        self.page_entry = ttk.Entry(
            page_frame,
            textvariable=self.page_number_var,
            width=6,
            validate="key",
            validatecommand=validate_page,
        )
        self.page_entry.grid(row=0, column=1, padx=4)
        self.page_entry.bind("<FocusOut>", self._clamp_page_number)
        ttk.Checkbutton(
            page_frame,
            text="Última página",
            variable=self.last_page_var,
            command=self._toggle_page_entry,
        ).grid(row=0, column=2, padx=8)
        self._toggle_page_entry()
        row += 1

        ttk.Separator(right).grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
        row += 1

        names = ttk.Frame(right)
        names.grid(row=row, column=0, columnspan=2, sticky="w", **pad)
        ttk.Label(names, text="Nombres").grid(row=0, column=0)
        ttk.Entry(names, textvariable=self.vars["SIGNER_FIRST_NAME"], width=16).grid(row=0, column=1, padx=4)
        ttk.Label(names, text="Apellidos").grid(row=0, column=2)
        ttk.Entry(names, textvariable=self.vars["SIGNER_LAST_NAME"], width=16).grid(row=0, column=3, padx=4)
        row += 1

        name_date = ttk.Frame(right)
        name_date.grid(row=row, column=0, columnspan=2, sticky="w", **pad)
        for r, (name_key, name_label, date_key, date_label) in enumerate([
            ("NAME_POS_X", "Nombre · X", "DATE_POS_X", "Fecha · X"),
            ("NAME_POS_Y", "Nombre · Y", "DATE_POS_Y", "Fecha · Y"),
            ("NAME_FONT_SIZE", "Nombre · tamaño", "DATE_FONT_SIZE", "Fecha · tamaño"),
        ]):
            ttk.Label(name_date, text=name_label).grid(row=r, column=0, sticky="w", pady=2)
            ttk.Entry(name_date, textvariable=self.vars[name_key], width=8).grid(
                row=r, column=1, sticky="w", padx=(4, 20), pady=2
            )
            ttk.Label(name_date, text=date_label).grid(row=r, column=2, sticky="w", pady=2)
            ttk.Entry(name_date, textvariable=self.vars[date_key], width=8).grid(
                row=r, column=3, sticky="w", padx=4, pady=2
            )
        row += 1

        self._add_entry(right, row, "Formato de fecha", "DATE_FORMAT")
        row += 1
        self._add_entry(right, row, "Fuente (.ttf)", "FONT_PATH", browse=FONT_FILETYPES)
        row += 1
        self._add_entry(right, row, "Color R,G,B", "TEXT_COLOR")
        row += 1

        footer = ttk.Frame(container, padding=(0, 10, 0, 0))
        footer.grid(row=1, column=0, columnspan=2, sticky="ew")
        footer.columnconfigure(0, weight=1)

        status_box = ttk.Frame(footer)
        status_box.grid(row=0, column=0, sticky="ew")
        self.status_label = ttk.Label(status_box, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(status_box, length=320, mode="determinate")
        self.progress.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        buttons = ttk.Frame(footer)
        buttons.grid(row=0, column=1, rowspan=2, sticky="e")
        self.sign_button = ttk.Button(buttons, text="FIRMAR", command=self.on_sign)
        self.sign_button.grid(row=0, column=0, padx=4)

        self._set_status_idle()

    def _add_entry(self, parent, row, label, key, width=28, show=None, browse=None):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=3)
        entry = ttk.Entry(parent, textvariable=self.vars[key], width=width, show=show or "")
        entry.grid(row=row, column=1, sticky="w", padx=8, pady=3)
        if key == "IN_DIR":
            entry.bind("<FocusOut>", lambda e: self.refresh_pdf_count())
        if browse is not None:
            ttk.Button(
                parent, text="…", width=3, command=lambda: self._browse(key, browse)
            ).grid(row=row, column=2, sticky="w", padx=(0, 8), pady=3)
        return entry

    def _browse(self, key, kind):
        current = self._resolve_path(self.vars[key].get().strip() or ".")
        initial_dir = current if current.is_dir() else current.parent
        if not initial_dir.is_dir():
            initial_dir = app_dir()

        if kind == "dir":
            chosen = filedialog.askdirectory(initialdir=str(initial_dir), parent=self.root)
        else:
            chosen = filedialog.askopenfilename(
                initialdir=str(initial_dir), filetypes=kind, parent=self.root
            )
        if chosen:
            self.vars[key].set(chosen)
            if key == "IN_DIR":
                self.refresh_pdf_count()

    def _toggle_page_entry(self):
        editable = not self.last_page_var.get()
        self.page_entry.configure(state="normal" if editable else "disabled")
        if editable and not self.page_number_var.get().strip():
            self.page_number_var.set("1")

    def _validate_page_input(self, proposed: str) -> bool:
        # Solo dígitos (o vacío, para poder borrar); el mínimo de 1 se aplica
        # al salir del campo en _clamp_page_number, no mientras se escribe.
        return proposed == "" or proposed.isdigit()

    def _clamp_page_number(self, _event=None):
        value = self.page_number_var.get().strip()
        page = int(value) if value else 0
        self.page_number_var.set(str(max(page, 1)))

    # --- estado / helpers ---

    def _set_status_idle(self):
        n = len(list_pdfs(self._resolve_in_dir()))
        self.status_var.set(f"Listo. {n} PDF en la carpeta de entrada.")
        self.progress["value"] = 0
        self.progress["maximum"] = max(n, 1)

    def _resolve_path(self, raw: str) -> Path:
        p = Path(raw).expanduser()
        return p if p.is_absolute() else (app_dir() / p).resolve()

    def _resolve_in_dir(self) -> Path:
        return self._resolve_path(self.vars["IN_DIR"].get().strip() or "./in")

    def refresh_pdf_count(self):
        if not self.running:
            self._set_status_idle()

    def _collect_raw_values(self) -> dict:
        raw = {key: var.get() for key, var in self.vars.items()}
        raw["SIGN_PAGE"] = "last" if self.last_page_var.get() else (self.page_number_var.get().strip() or "1")
        return raw

    # --- firmar ---

    def on_sign(self):
        if self.running:
            return

        raw = self._collect_raw_values()
        try:
            cfg = build_config(raw, app_dir(), config_env_path())
        except ValueError as e:
            messagebox.showerror("Configuración inválida", str(e))
            return

        pdfs = list_pdfs(cfg.in_dir)
        if not pdfs:
            messagebox.showinfo("Sin archivos", f"No se encontraron PDFs en {cfg.in_dir}")
            return

        password = cfg.pfx_password
        if not password:
            password = self._ask_password(cfg.pfx_path.name)
            if password is None:
                return

        raw["PFX_PASSWORD"] = password
        try:
            write_config_env(raw, self.remember_var.get())
        except OSError as e:
            messagebox.showwarning(
                "No se pudo guardar la configuración",
                f"El firmado va a continuar, pero no se pudo guardar config.env:\n{e}",
            )

        self.running = True
        self.sign_button.configure(state="disabled")
        self.progress["value"] = 0
        self.progress["maximum"] = len(pdfs)
        self.status_var.set("Abriendo certificado…")

        def worker():
            try:
                sign_batch(cfg, password, on_progress=self._on_progress)
            except ValueError as e:
                self.queue.put(("error", str(e)))
            else:
                self.queue.put(("done", str(cfg.out_dir)))

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(80, self._poll_queue)

    def _ask_password(self, pfx_name: str):
        top = tk.Toplevel(self.root)
        top.title("Clave del certificado")
        top.resizable(False, False)
        top.transient(self.root)
        top.grab_set()

        ttk.Label(top, text=f"Clave del certificado {pfx_name}:").grid(row=0, column=0, padx=10, pady=(10, 4))
        pwd_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=pwd_var, show="*", width=28)
        entry.grid(row=1, column=0, padx=10, pady=4)
        entry.focus_set()

        result = {"value": None}

        def confirm(_event=None):
            result["value"] = pwd_var.get()
            top.destroy()

        def cancel():
            top.destroy()

        entry.bind("<Return>", confirm)
        buttons = ttk.Frame(top)
        buttons.grid(row=2, column=0, pady=(4, 10))
        ttk.Button(buttons, text="Cancelar", command=cancel).grid(row=0, column=0, padx=4)
        ttk.Button(buttons, text="Continuar", command=confirm).grid(row=0, column=1, padx=4)

        self.root.wait_window(top)
        return result["value"] or None

    def _on_progress(self, done, total, name, status, msg):
        self.queue.put(("progress", done, total, name, status, msg))

    def _poll_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if item[0] == "progress":
                    _, done, total, name, status, msg = item
                    self.progress["maximum"] = total
                    self.progress["value"] = done
                    line = f"{status}" + (f" ({msg})" if msg else "")
                    self.status_var.set(f"Firmando {done} de {total} · {name} · {line}")
                elif item[0] == "done":
                    self.status_var.set(f"Listo · PDFs firmados guardados en {item[1]}")
                    self.running = False
                    self.sign_button.configure(state="normal")
                elif item[0] == "error":
                    messagebox.showerror("No se pudo firmar", item[1])
                    self.status_var.set("Error al firmar. Revisa la clave y la configuración.")
                    self.running = False
                    self.sign_button.configure(state="normal")
        except queue.Empty:
            pass

        if self.running:
            self.root.after(80, self._poll_queue)


def main() -> int:
    root = tk.Tk()
    FirmadorGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
