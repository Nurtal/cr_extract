"""Couverture des tags : quels tags annotés disposent d'un extracteur ?

Croise les tags présents dans la vérité terrain (corpus / CSV) avec les
extracteurs enregistrés, pour mettre en évidence ce qui **n'est pas encore
couvert** (p. ex. les tags expérimentaux ajoutés en vue d'un travail futur).

Un tag est dit *couvert* s'il existe un extracteur enregistré pour cette clé.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable

from cr_extract.chargement import CompteRendu
from cr_extract.modele import CHAMPS, CHAMPS_PAR_CLE
from cr_extract.extracteurs import extracteurs_disponibles


@dataclass
class CouvertureTag:
    """Couverture d'un tag observé dans la vérité terrain."""

    tag: str
    occurrences: int = 0                       # nombre de CR annotés sur ce tag
    valeurs: Counter = field(default_factory=Counter)  # distribution des valeurs gold
    dans_catalogue: bool = False               # déclaré dans modele.CHAMPS
    a_extracteur: bool = False                 # extracteur enregistré

    @property
    def couvert(self) -> bool:
        return self.a_extracteur


def couverture_tags(crs: Iterable[CompteRendu]) -> dict[str, CouvertureTag]:
    """Calcule la couverture de chaque tag rencontré dans ``crs``.

    Inclut aussi les champs du catalogue jamais annotés (occurrences = 0), pour
    repérer un champ déclaré mais absent des données.
    """
    extracteurs = extracteurs_disponibles()
    couverture: dict[str, CouvertureTag] = {}

    def _entree(tag: str) -> CouvertureTag:
        if tag not in couverture:
            couverture[tag] = CouvertureTag(
                tag=tag,
                dans_catalogue=tag in CHAMPS_PAR_CLE,
                a_extracteur=tag in extracteurs,
            )
        return couverture[tag]

    # Champs du catalogue d'abord (même non annotés), puis tags rencontrés.
    for champ in CHAMPS:
        _entree(champ.cle)
    for cr in crs:
        for tag, valeur in cr.gold.items():
            entree = _entree(tag)
            entree.occurrences += 1
            entree.valeurs[valeur] += 1

    return couverture


def tags_non_couverts(couverture: dict[str, CouvertureTag]) -> list[str]:
    """Tags annotés (occurrences > 0) sans extracteur, triés par fréquence."""
    manquants = [c for c in couverture.values() if c.occurrences > 0 and not c.couvert]
    manquants.sort(key=lambda c: (-c.occurrences, c.tag))
    return [c.tag for c in manquants]


def rapport_couverture(couverture: dict[str, CouvertureTag]) -> str:
    """Rapport markdown : table par tag + synthèse des tags non couverts."""
    lignes = [
        "# Couverture des tags",
        "",
        "| Tag | Couvert | Occurrences | Catalogue | Valeurs |",
        "|-----|---------|-------------|-----------|---------|",
    ]
    # Couverts d'abord (par fréquence), puis non couverts.
    items = sorted(
        couverture.values(),
        key=lambda c: (not c.couvert, -c.occurrences, c.tag),
    )
    for c in items:
        marque = "✓" if c.couvert else "✗"
        distrib = ", ".join(f"{v}:{n}" for v, n in c.valeurs.most_common()) or "—"
        lignes.append(
            f"| `{c.tag}` | {marque} | {c.occurrences} | "
            f"{'oui' if c.dans_catalogue else 'non'} | {distrib} |"
        )

    couverts = sum(1 for c in couverture.values() if c.couvert and c.occurrences > 0)
    observes = sum(1 for c in couverture.values() if c.occurrences > 0)
    manquants = tags_non_couverts(couverture)
    lignes += [
        "",
        f"**{couverts}/{observes} tags annotés couverts par un extracteur.**",
    ]
    if manquants:
        lignes.append("Non couverts : " + ", ".join(f"`{t}`" for t in manquants) + ".")
    else:
        lignes.append("Tous les tags annotés sont couverts. 🎉")
    return "\n".join(lignes)
