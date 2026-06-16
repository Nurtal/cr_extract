"""Registre des extracteurs, indexés par clé interne de champ.

Vide en Phase 1 : les extracteurs seront enregistrés ici au fil des phases 2-4
via le décorateur :func:`enregistrer`.
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
