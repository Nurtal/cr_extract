"""Normalisation du texte en amont des extracteurs.

On produit une forme « simplifiée » (minuscules, sans accents, espaces
homogénéisés) qui rend les regex plus robustes, tout en conservant le texte
d'origine pour restituer les preuves.
"""

from __future__ import annotations

import re
import unicodedata

_ESPACES = re.compile(r"\s+")


def retirer_accents(texte: str) -> str:
    """Retire les diacritiques (é -> e, ï -> i, ç -> c…)."""
    decompose = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in decompose if not unicodedata.combining(c))


def normaliser(texte: str) -> str:
    """Forme normalisée utilisée pour le matching regex.

    - passage en minuscules ;
    - suppression des accents ;
    - homogénéisation des apostrophes (typographiques -> ``'``) ;
    - réduction des espaces/sauts de ligne multiples à une espace simple.

    Le texte d'origine n'est pas modifié : il reste disponible pour la preuve.
    """
    texte = texte.replace("’", "'").replace("ʼ", "'")
    texte = retirer_accents(texte)
    texte = texte.lower()
    texte = _ESPACES.sub(" ", texte)
    return texte.strip()
