"""Corpus annoté sous forme de fichiers JSON (un par compte rendu).

Chaque compte rendu est un fichier JSON autonome :

```json
{
  "id": "cr_000",
  "texte": "COMPTE RENDU ...",
  "tags": {
    "situation_professionnelle": "inactif",
    "alcool": "True",
    ...
  }
}
```

Les ``tags`` sont les annotations de référence (gold), indexées par clé interne
de champ (cf. :data:`cr_extract.modele.CHAMPS`). Les valeurs reprennent les
chaînes canoniques du projet (``"True"`` / ``"False"`` / ``"NA"`` pour les
booléens, libellés pour les catégoriels, nombre en chaîne pour les numériques),
ce qui permet une comparaison directe avec les prédictions.

Format pensé pour être **édité à la main** et **étendu** :

- ajouter un compte rendu = déposer un nouveau fichier JSON dans le dossier ;
- annoter « plus ou moins » de tags = mettre/retirer des entrées de ``tags``
  (un tag absent est simplement ignoré à l'évaluation) ;
- introduire un **nouveau tag** (pour un travail ultérieur) = ajouter une clé
  inédite ; elle est conservée et chargée, prête pour un futur extracteur.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Union

from cr_extract.chargement import CompteRendu, charger_csv
from cr_extract.modele import CHAMPS


def ecrire_corpus(
    crs: Iterable[CompteRendu],
    dossier: Union[str, Path],
    prefixe: str = "cr_",
    largeur: int = 3,
) -> list[Path]:
    """Écrit un fichier JSON par compte rendu dans ``dossier``.

    Les tags connus sont ordonnés selon le catalogue, puis suivis d'éventuels
    tags supplémentaires (ordre d'apparition). Renvoie la liste des chemins
    écrits.
    """
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    chemins: list[Path] = []
    for cr in crs:
        identifiant = f"{prefixe}{cr.index:0{largeur}d}"
        chemin = dossier / f"{identifiant}.json"
        donnees = {
            "id": identifiant,
            "texte": cr.texte,
            "tags": _ordonner_tags(cr.gold),
        }
        chemin.write_text(
            json.dumps(donnees, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        chemins.append(chemin)
    return chemins


def charger_corpus(dossier: Union[str, Path]) -> list[CompteRendu]:
    """Charge tous les comptes rendus JSON d'un dossier (tri par nom de fichier).

    Renvoie des :class:`CompteRendu` dont ``gold`` contient les tags annotés.
    Les tags absents d'un fichier restent absents (annotation partielle), ce que
    l'évaluation gère naturellement.
    """
    dossier = Path(dossier)
    crs: list[CompteRendu] = []
    for index, chemin in enumerate(sorted(dossier.glob("*.json"))):
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
        crs.append(
            CompteRendu(
                texte=donnees.get("texte", ""),
                gold=dict(donnees.get("tags", {})),
                index=index,
            )
        )
    return crs


def csv_vers_corpus(
    csv_chemin: Union[str, Path],
    dossier: Union[str, Path],
) -> list[Path]:
    """Convertit le CSV de référence en corpus JSON (un fichier par ligne)."""
    return ecrire_corpus(charger_csv(csv_chemin), dossier)


def _ordonner_tags(gold: dict[str, str]) -> dict[str, str]:
    """Tags du catalogue d'abord (dans l'ordre), puis tags supplémentaires."""
    ordonnes = {champ.cle: gold[champ.cle] for champ in CHAMPS if champ.cle in gold}
    for cle, valeur in gold.items():
        if cle not in ordonnes:
            ordonnes[cle] = valeur
    return ordonnes
