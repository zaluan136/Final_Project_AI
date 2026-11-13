"""Load the shared Qt stylesheet independently of the working directory."""

from pathlib import Path

MATERIAL_QSS = Path(__file__).with_name("theme.qss").read_text(encoding="utf-8")
