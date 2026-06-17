"""Registre des extracteurs, indexés par clé interne de champ.

Les extracteurs s'enregistrent via le décorateur :func:`enregistrer`. Importer
ce package suffit à peupler ``REGISTRE`` : les modules d'extracteurs sont chargés
en fin de fichier (après définition du décorateur, pour éviter les imports
circulaires).
"""

from __future__ import annotations

from typing import Callable

from cr_extract.modele import Extracteur

# clé interne de champ -> extracteur
REGISTRE: dict[str, Extracteur] = {}


def enregistrer(cle_champ: str) -> Callable[[type], type]:
    """Décorateur de classe pour inscrire un extracteur dans le registre."""

    def _decorateur(classe: type) -> type:
        REGISTRE[cle_champ] = classe()
        return classe

    return _decorateur


def extracteurs_disponibles() -> dict[str, Extracteur]:
    """Renvoie une copie du registre courant."""
    return dict(REGISTRE)


# Chargement des extracteurs concrets : l'import déclenche l'enregistrement via
# le décorateur. Placé en fin de module pour que ``enregistrer`` existe déjà.
from cr_extract.extracteurs import (  # noqa: E402,F401
    conjugal,
    juridique,
    logement,
    professionnel,
    sevrage,
    substances,
)
