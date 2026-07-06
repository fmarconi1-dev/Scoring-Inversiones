"""Carga y valida config.json. Punto unico de verdad para universo y umbrales."""
import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "config.json"


def cargar_config() -> dict:
    """Devuelve el config como dict. Lanza si el archivo no existe o es invalido."""
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(f"No se encuentra config.json en {_CONFIG_PATH}")
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    _validar(cfg)
    return cfg


def _validar(cfg: dict) -> None:
    for clave in ("universo", "umbrales_fundamentales", "umbrales_tecnicos", "clasificacion"):
        if clave not in cfg:
            raise ValueError(f"config.json invalido: falta la clave '{clave}'")
    if not cfg["universo"]:
        raise ValueError("config.json invalido: el universo esta vacio")


if __name__ == "__main__":
    c = cargar_config()
    print(f"OK - {len(c['universo'])} tickers, corte fund={c['clasificacion']['corte_fundamental']}, "
          f"tec={c['clasificacion']['corte_tecnico']}")
