"""Ajoute la racine du dépôt au sys.path pour que ``import cr_extract``
fonctionne lors de l'exécution de pytest."""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))
