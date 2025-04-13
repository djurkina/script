#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shot‑Folder‑CLI – CLI и интерактивный бот для создания структуры шотов
с поддержкой Shared Drives (общих дисков).
"""

import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Union

import typer
from google.oauth2.service_account import Credentials as SA_Credentials
from googleapiclient.discovery import build
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from rich.console import Console
from rich.progress import track

app = typer.Typer(add_completion=False)
console = Console()

SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_KEY_FILE = Path("service_account.json")
CONFIG_FILE = Path("config.json")
STRUCTURE_FILE = Path("structure.json")

FolderNode = Union[List[str], Dict[str, "FolderNode"]]

# ————— Google Drive helper —————
def _build_service():
    if not SERVICE_KEY_FILE.exists():
        console.print("[bold red]service_account.json не найден[/]")
        raise typer.Exit(1)
    creds = SA_Credentials.from_service_account_file(str(SERVICE_KEY_FILE), scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)

@retry(wait=wait_exponential(multiplier=2, min=2, max=32), stop=stop_after_attempt(5), retry=retry_if_exception_type(Exception))
def create_folder(name: str, parent_id: str, service) -> str:
    query = (
        "mimeType='application/vnd.google-apps.folder' "
        f"and name='{name}' and '{parent_id}' in parents and trashed=false"
    )
    res = service.files().list(
        q=query,
        fields="files(id)",
        includeItemsFromAllDrives=True,
        supportsAllDrives=True
    ).execute()
    if res.get("files"):
        return res["files"][0]["id"]

    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    return service.files().create(
        body=meta,
        fields="id",
        supportsAllDrives=True
    ).execute()["id"]

# ————— Utils —————
def load_structure() -> Dict[str, FolderNode]:
    if not STRUCTURE_FILE.exists():
        console.print(f"[bold red]{STRUCTURE_FILE} не найден.[/]")
        raise typer.Exit(1)
    return json.loads(STRUCTURE_FILE.read_text(encoding="utf-8"))

def load_root_id() -> str:
    if not CONFIG_FILE.exists():
        console.print("[bold red]config.json не найден[/]")
        raise typer.Exit(1)
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))["google_root_id"]

def build_structure(parent_id: str, structure: Dict[str, FolderNode], service):
    for name, sub in structure.items():
        fid = create_folder(name, parent_id, service)
        if isinstance(sub, dict):
            build_structure(fid, sub, service)
        else:
            for leaf in sub:
                create_folder(leaf, fid, service)

def format_shot_name(index: int, pad: int) -> str:
    return f"shot_{index * 10:0{pad}d}"

SHOT_RE = re.compile(r"^shot_\d+$")
def validate_shot_name(name: str) -> bool:
    return bool(SHOT_RE.fullmatch(name))

# ————— Typer команды —————
@app.command()
def create(num: int = typer.Argument(...), pad: int = typer.Option(None), dry: bool = False):
    """Создать N шотов с шагом 10 (shot_0010 …)."""
    if num <= 0:
        console.print("[red]Число шотов должно быть > 0[/]")
        raise typer.Exit(1)
    pad = pad or max(4, len(str(num * 10)))
    struct = load_structure()
    root_id = load_root_id()
    service = None if dry else _build_service()
    for i in track(range(1, num + 1), description="Создаю шоты"):
        name = format_shot_name(i, pad)
        if dry:
            console.print(name)
        else:
            fid = create_folder(name, root_id, service)
            build_structure(fid, struct, service)
    console.print("[green]Готово![/]")

@app.command()
def single(name: str, dry: bool = False):
    """Создать один шот по имени (shot_0055)."""
    if not validate_shot_name(name):
        console.print("[red]Неверный формат имени (shot_####)[/]")
        raise typer.Exit(1)
    if dry:
        console.print(f"[yellow]DRY-RUN[/]: {name}")
        return
    struct = load_structure()
    root_id = load_root_id()
    service = _build_service()
    fid = create_folder(name, root_id, service)
    build_structure(fid, struct, service)
    console.print(f"[green]Папка {name} создана[/]")

@app.command()
def verify():
    """Проверить, что структура создана корректно."""
    struct = load_structure()
    root_id = load_root_id()
    service = _build_service()
    missing = False

    def _v(pid, node, prefix):
        nonlocal missing
        for name, sub in node.items():
            q = (
                "mimeType='application/vnd.google-apps.folder' "
                f"and name='{name}' and '{pid}' in parents and trashed=false"
            )
            res = service.files().list(
                q=q,
                fields="files(id)",
                includeItemsFromAllDrives=True,
                supportsAllDrives=True
            ).execute()
            if not res.get("files"):
                console.print(f"[red]Отсутствует:[/] {prefix}/{name}")
                missing = True
            else:
                fid = res["files"][0]["id"]
                if isinstance(sub, dict):
                    _v(fid, sub, f"{prefix}/{name}")
                else:
                    for leaf in sub:
                        q2 = (
                            "mimeType='application/vnd.google-apps.folder' "
                            f"and name='{leaf}' and '{fid}' in parents and trashed=false"
                        )
                        res2 = service.files().list(
                            q=q2,
                            fields="files(id)",
                            includeItemsFromAllDrives=True,
                            supportsAllDrives=True
                        ).execute()
                        if not res2.get("files"):
                            console.print(f"[red]Отсутствует:[/] {prefix}/{name}/{leaf}")
                            missing = True
    _v(root_id, struct, "<root>")
    console.print("[green]Проверка завершена[/]" if not missing else "[yellow]Обнаружены пропущенные папки[/]")

# ————— Бесконечный режим —————
def _interactive_loop():
    while True:
        try:
            user_inp = input("\n▶ Введите число шотов, имя (shot_####) или 'verify' (Enter — выход): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_inp:
            break
        sys.argv = [sys.argv[0]]
        if user_inp.lower() == "verify":
            sys.argv.append("verify")
        elif user_inp.isdigit():
            sys.argv.extend(["create", user_inp])
        else:
            sys.argv.extend(["single", user_inp])
        try:
            app()
        except SystemExit:
            pass
    console.print("[cyan]Выход[/]")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        _interactive_loop()
    else:
        app()
