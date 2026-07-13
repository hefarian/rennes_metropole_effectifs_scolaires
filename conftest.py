"""Configuration pytest : résolution des imports pour tous les packages du projet.

- Ajoute la racine du projet (.) au sys.path → import `api` fonctionne.
- Ajoute le répertoire `src/` au sys.path → import `p13` fonctionne.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
SRC_DIR = PROJECT_ROOT / "src"

# insert(0, ...) pour que ces chemins aient priorité sur les packages système
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
