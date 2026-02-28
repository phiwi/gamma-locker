import json
from pathlib import Path
from typing import Any

CONFIG_FILE = Path(__file__).with_name("paths_config.json")

DEFAULT_PATHS_CONFIG = {
    "save_dir": "/mnt/c/G.A.M.M.A/Anomaly-1.5.3-Full.2/appdata/savedgames/",
    "scan_paths": [
        "/mnt/c/G.A.M.M.A/MO2/mods",
        "/mnt/c/G.A.M.M.A/Anomaly-1.5.3-Full.2/gamedata/configs/items/weapons",
    ],
    "text_paths": [
        "/mnt/c/G.A.M.M.A/MO2/mods",
        "/mnt/c/G.A.M.M.A/Anomaly-1.5.3-Full.2/gamedata/configs/text/eng",
    ],
    "texture_paths": [
        "/mnt/c/G.A.M.M.A/MO2/mods",
        "/mnt/c/G.A.M.M.A/Anomaly-1.5.3-Full.2/gamedata/textures",
    ],
}


def load_paths_config() -> dict[str, Any]:
    config = dict(DEFAULT_PATHS_CONFIG)
    if not CONFIG_FILE.exists():
        return config

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
            user_cfg = json.load(fh)
    except Exception:
        return config

    if not isinstance(user_cfg, dict):
        return config

    for key in config.keys():
        value = user_cfg.get(key)
        if value is None:
            continue
        config[key] = value

    return config


def get_path(key: str, fallback: str = "") -> Path:
    cfg = load_paths_config()
    value = cfg.get(key, fallback)
    return Path(str(value))


def get_path_list(key: str) -> list[Path]:
    cfg = load_paths_config()
    values = cfg.get(key, [])
    if not isinstance(values, list):
        return []
    return [Path(str(item)) for item in values]
