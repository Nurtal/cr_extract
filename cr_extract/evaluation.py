"""Harnais d'évaluation : prédictions vs vérité terrain.

Calcule, par champ, l'exactitude (accuracy) et une matrice de confusion mettant
en évidence les confusions critiques (notamment ``False`` vs ``NA``). Produit un
rapport texte/markdown et la liste des lignes en échec, pour piloter l'itération
sur les regex (Phase 5 de la ROADMAP).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Union

from cr_extract.chargement import charger_csv, CompteRendu
from cr_extract.modele import CHAMPS
from cr_extract.pipeline import extraire_tout


@dataclass
class ScoreChamp:
    """Résultat d'évaluation pour un champ."""

    cle: str
    total: int = 0
    corrects: int = 0
    # matrice[(gold, pred)] = nombre d'occurrences
    matrice: Counter = field(default_factory=Counter)
    # (index_ligne, gold, pred) des erreurs
    erreurs: list = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return self.corrects / self.total if self.total else 0.0


def evaluer(crs: Iterable[CompteRendu]) -> dict[str, ScoreChamp]:
    """Évalue les extracteurs sur des comptes rendus annotés (champ ``gold``)."""
    scores = {champ.cle: ScoreChamp(cle=champ.cle) for champ in CHAMPS}
    for cr in crs:
        if not cr.gold:
            continue
        predictions = extraire_tout(cr.texte)
        for champ in CHAMPS:
            gold = cr.gold.get(champ.cle)
            if gold is None:
                continue
            pred = predictions[champ.cle].valeur
            score = scores[champ.cle]
            score.total += 1
            score.matrice[(gold, pred)] += 1
            if pred == gold:
                score.corrects += 1
            else:
                score.erreurs.append((cr.index, gold, pred))
    return scores


def evaluer_fichier(chemin: Union[str, Path]) -> dict[str, ScoreChamp]:
    """Charge un CSV annoté et renvoie les scores par champ."""
    return evaluer(charger_csv(chemin))


def evaluer_corpus(dossier: Union[str, Path]) -> dict[str, ScoreChamp]:
    """Charge un corpus JSON (un fichier par CR) et renvoie les scores."""
    from cr_extract.corpus import charger_corpus

    return evaluer(charger_corpus(dossier))


def rapport_markdown(scores: dict[str, ScoreChamp]) -> str:
    """Produit un rapport markdown : accuracy par champ + accuracy globale."""
    lignes = ["# Rapport d'évaluation CR Extract", "", "| Champ | Accuracy | Corrects / Total |", "|---|---|---|"]
    total = corrects = 0
    for champ in CHAMPS:
        s = scores[champ.cle]
        total += s.total
        corrects += s.corrects
        lignes.append(f"| {champ.cle} | {s.accuracy:.0%} | {s.corrects}/{s.total} |")
    globale = corrects / total if total else 0.0
    lignes += ["", f"**Accuracy globale : {globale:.1%}** ({corrects}/{total})"]
    return "\n".join(lignes)


def rapport_confusions(scores: dict[str, ScoreChamp]) -> str:
    """Détaille les confusions (gold -> pred) pour chaque champ imparfait."""
    lignes = ["# Confusions par champ", ""]
    for champ in CHAMPS:
        s = scores[champ.cle]
        confusions = {k: v for k, v in s.matrice.items() if k[0] != k[1]}
        if not confusions:
            continue
        lignes.append(f"## {champ.cle} (accuracy {s.accuracy:.0%})")
        for (gold, pred), n in sorted(confusions.items(), key=lambda x: -x[1]):
            lignes.append(f"- gold=`{gold}` -> pred=`{pred}` : {n}")
        lignes.append("")
    return "\n".join(lignes)
