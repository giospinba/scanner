#!/usr/bin/env python3
"""ScannerPy: semplice scanner di sistema con CLI e GUI."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


@dataclass
class CheckResult:
    name: str
    status: str
    message: str


@dataclass
class ScanReport:
    scanned_at: str
    hostname: str
    os_name: str
    os_version: str
    python_version: str
    checks: list[CheckResult]

    def to_dict(self) -> dict:
        return {
            "scanned_at": self.scanned_at,
            "hostname": self.hostname,
            "os_name": self.os_name,
            "os_version": self.os_version,
            "python_version": self.python_version,
            "checks": [asdict(c) for c in self.checks],
        }


class SystemScanner:
    def __init__(
        self,
        path_to_check: Path | None = None,
        disk_warn_threshold: float = 0.90,
        disk_critical_threshold: float = 0.97,
    ) -> None:
        self.path_to_check = path_to_check or Path.home()
        self.disk_warn_threshold = disk_warn_threshold
        self.disk_critical_threshold = disk_critical_threshold

    def run_all_checks(self) -> ScanReport:
        checks = [
            self.check_python_version(),
            self.check_working_directory_access(),
            self.check_disk_space(),
            self.check_network_dns(),
            self.check_common_tooling(),
        ]
        return ScanReport(
            scanned_at=datetime.now(timezone.utc).isoformat(),
            hostname=platform.node() or "unknown-host",
            os_name=platform.system() or "unknown-os",
            os_version=platform.version() or "unknown-version",
            python_version=platform.python_version(),
            checks=checks,
        )

    def check_python_version(self) -> CheckResult:
        major, minor, *_ = platform.python_version_tuple()
        version = f"{major}.{minor}"
        if int(major) < 3 or (int(major) == 3 and int(minor) < 10):
            return CheckResult(
                name="Python version",
                status="warning",
                message=f"Versione Python {version}: consigliato >= 3.10",
            )
        return CheckResult(
            name="Python version",
            status="ok",
            message=f"Versione Python {version} supportata",
        )

    def check_working_directory_access(self) -> CheckResult:
        test_file = self.path_to_check / ".scannerpy_write_test"
        try:
            self.path_to_check.mkdir(parents=True, exist_ok=True)
            test_file.write_text("ok", encoding="utf-8")
            content = test_file.read_text(encoding="utf-8")
            if content != "ok":
                return CheckResult(
                    name="Filesystem access",
                    status="critical",
                    message=f"Lettura/scrittura inconsistente in {self.path_to_check}",
                )
            return CheckResult(
                name="Filesystem access",
                status="ok",
                message=f"Permessi lettura/scrittura validi in {self.path_to_check}",
            )
        except Exception as exc:
            return CheckResult(
                name="Filesystem access",
                status="critical",
                message=f"Errore accesso filesystem: {exc}",
            )
        finally:
            try:
                if test_file.exists():
                    test_file.unlink()
            except OSError:
                pass

    def check_disk_space(self) -> CheckResult:
        usage = shutil.disk_usage(self.path_to_check)
        used_ratio = usage.used / usage.total if usage.total else 0
        percent = used_ratio * 100
        if used_ratio >= self.disk_critical_threshold:
            return CheckResult(
                name="Disk usage",
                status="critical",
                message=f"Disco quasi pieno ({percent:.1f}% usato)",
            )
        if used_ratio >= self.disk_warn_threshold:
            return CheckResult(
                name="Disk usage",
                status="warning",
                message=f"Disco in soglia attenzione ({percent:.1f}% usato)",
            )
        return CheckResult(
            name="Disk usage",
            status="ok",
            message=f"Spazio disco OK ({percent:.1f}% usato)",
        )

    def check_network_dns(self) -> CheckResult:
        try:
            result = subprocess.run(
                ["python3", "-c", "import socket; socket.gethostbyname('openai.com')"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except Exception as exc:
            return CheckResult(
                name="Network DNS",
                status="warning",
                message=f"Controllo DNS non riuscito: {exc}",
            )

        if result.returncode == 0:
            return CheckResult(
                name="Network DNS",
                status="ok",
                message="Risoluzione DNS funzionante",
            )

        stderr = (result.stderr or "errore sconosciuto").strip()
        return CheckResult(
            name="Network DNS",
            status="warning",
            message=f"Problema DNS: {stderr}",
        )

    def check_common_tooling(self) -> CheckResult:
        missing = [tool for tool in ("git", "python3") if shutil.which(tool) is None]
        if missing:
            return CheckResult(
                name="Tooling",
                status="warning",
                message=f"Tool mancanti: {', '.join(missing)}",
            )
        return CheckResult(
            name="Tooling",
            status="ok",
            message="Tool base installati (git, python3)",
        )


STATUS_COLOR = {
    "ok": "#1f9d55",
    "warning": "#d97706",
    "critical": "#dc2626",
}


def _load_tkinter():
    import tkinter as tk
    from tkinter import ttk

    return tk, ttk


def launch_gui(scanner: SystemScanner) -> None:
    tk, ttk = _load_tkinter()
    root = tk.Tk()
    root.title("ScannerPy - System Health")
    root.geometry("980x640")
    root.minsize(900, 560)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("Title.TLabel", font=("Segoe UI", 19, "bold"), foreground="#0f172a")
    style.configure("Sub.TLabel", font=("Segoe UI", 10), foreground="#475569")
    style.configure("Ok.TLabel", font=("Segoe UI", 10, "bold"), foreground=STATUS_COLOR["ok"])
    style.configure("Warning.TLabel", font=("Segoe UI", 10, "bold"), foreground=STATUS_COLOR["warning"])
    style.configure("Critical.TLabel", font=("Segoe UI", 10, "bold"), foreground=STATUS_COLOR["critical"])
    style.configure("Card.TFrame", background="#f8fafc")

    container = ttk.Frame(root, padding=16)
    container.pack(fill="both", expand=True)

    header = ttk.Frame(container)
    header.pack(fill="x")
    ttk.Label(header, text="ScannerPy", style="Title.TLabel").pack(anchor="w")
    ttk.Label(
        header,
        text="Controllo automatico del sistema (senza terminale)",
        style="Sub.TLabel",
    ).pack(anchor="w", pady=(4, 14))

    topbar = ttk.Frame(container)
    topbar.pack(fill="x", pady=(0, 12))

    summary_var = tk.StringVar(value="Premi 'Avvia scansione' per iniziare")
    ttk.Label(topbar, textvariable=summary_var, style="Sub.TLabel").pack(side="left")

    body = ttk.Frame(container, style="Card.TFrame", padding=12)
    body.pack(fill="both", expand=True)

    columns = ("check", "status", "message")
    tree = ttk.Treeview(body, columns=columns, show="headings", height=14)
    tree.heading("check", text="Controllo")
    tree.heading("status", text="Stato")
    tree.heading("message", text="Dettagli")
    tree.column("check", width=180, anchor="w")
    tree.column("status", width=90, anchor="center")
    tree.column("message", width=620, anchor="w")
    tree.pack(fill="both", expand=True)

    for key, color in STATUS_COLOR.items():
        tree.tag_configure(key, foreground=color)

    footer = ttk.Frame(container)
    footer.pack(fill="x", pady=(10, 0))

    def render_report(report: ScanReport) -> None:
        tree.delete(*tree.get_children())
        counts = {"ok": 0, "warning": 0, "critical": 0}
        for c in report.checks:
            counts[c.status] = counts.get(c.status, 0) + 1
            tree.insert("", "end", values=(c.name, c.status.upper(), c.message), tags=(c.status,))

        summary_var.set(
            f"Ultima scansione: {report.scanned_at} | OK: {counts['ok']} | "
            f"Warning: {counts['warning']} | Critical: {counts['critical']}"
        )

    running = {"value": False}

    def run_scan() -> None:
        if running["value"]:
            return
        running["value"] = True
        summary_var.set("Scansione in corso...")

        def worker() -> None:
            report = scanner.run_all_checks()

            def update_ui() -> None:
                render_report(report)
                running["value"] = False

            root.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    ttk.Button(footer, text="Avvia scansione", command=run_scan).pack(side="left")

    root.mainloop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ScannerPy - scanner sistema")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.home(),
        help="Percorso da usare per i controlli di filesystem/disco",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON in stdout",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Avvia interfaccia grafica",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scanner = SystemScanner(path_to_check=args.path)

    if args.gui:
        launch_gui(scanner)
        return 0

    report = scanner.run_all_checks()
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"ScannerPy @ {report.scanned_at}")
        print(f"Host: {report.hostname} | OS: {report.os_name} | Python: {report.python_version}")
        for check in report.checks:
            print(f"- [{check.status.upper():8}] {check.name}: {check.message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
