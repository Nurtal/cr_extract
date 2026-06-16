"""Chargement du CSV de comptes rendus médicaux.

Le fichier comporte un BOM (utf-8-sig), des champs multi-lignes entre guillemets
(gérés nativement par le module ``csv``) et 13 colonnes de vérité terrain en plus
de la colonne ``TEXTE``.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional, Union

from cr_extract.modele import CHAMPS_PAR_COLONNE

COLONNE_TEXTE = "TEXTE"


@dataclass
class CompteRendu:
    """Un compte rendu et, le cas échéant, ses annotations de référence.

    - ``texte`` : contenu de la colonne ``TEXTE``.
    - ``gold`` : valeurs de référence, indexées par clé interne de champ
      (``modele.Champ.cle``). Vide si le CSV ne contient que la colonne texte.
    - ``index`` : numéro de ligne (0-based) dans le fichier, utile pour le
      rapport d'erreurs.
    """

    texte: str
    gold: dict[str, str] = field(default_factory=dict)
    index: int = -1


def charger_csv(chemin: Union[str, Path]) -> list[CompteRendu]:
    """Charge l'ensemble des comptes rendus depuis un fichier CSV."""
    return list(iterer_csv(chemin))


def iterer_csv(chemin: Union[str, Path]) -> Iterator[CompteRendu]:
    """Itère paresseusement sur les comptes rendus d'un fichier CSV."""
    chemin = Path(chemin)
    with chemin.open(encoding="utf-8-sig", newline="") as f:
        lecteur = csv.DictReader(f)
        _verifier_entete(lecteur.fieldnames, chemin)
        for i, ligne in enumerate(lecteur):
            texte = (ligne.get(COLONNE_TEXTE) or "").strip()
            gold = {
                champ.cle: ligne[colonne]
                for colonne, champ in CHAMPS_PAR_COLONNE.items()
                if colonne in ligne and ligne[colonne] is not None
            }
            yield CompteRendu(texte=texte, gold=gold, index=i)


def _verifier_entete(entete: Optional[list[str]], chemin: Path) -> None:
    if not entete:
        raise ValueError(f"Fichier CSV vide ou sans en-tête : {chemin}")
    if COLONNE_TEXTE not in entete:
        raise ValueError(
            f"Colonne '{COLONNE_TEXTE}' absente de {chemin} ; "
            f"colonnes trouvées : {entete}"
        )
