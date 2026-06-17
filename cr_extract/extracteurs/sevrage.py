"""Extracteur des antécédents de sevrages compliqués (#5) — champ « difficile ».

Booléen 3 états avec **score de confiance**. Distinction clé :

- ``True``  : antécédent de sevrage **compliqué** — delirium tremens / DT,
  crises convulsives, sevrage(s) antérieur(s) qualifié(s) de compliqué/difficile.
- ``False`` : sevrage évoqué mais **sans** complication (« premier sevrage sans
  complication », « sevrage non compliqué », « pas d'antécédent de sevrage »).
- ``NA``    : aucun antécédent de sevrage évoqué (ou seulement un sevrage actuel
  / programmé, sans qualification de complication).

On s'appuie sur :func:`negation.est_nie` pour trancher « sevrages antérieurs
compliqués » (affirmé → True) de « sevrage non compliqué » (nié → False).
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

# Marqueurs de complication impliquant à eux seuls un antécédent de sevrage
# compliqué (le delirium tremens / les convulsions de sevrage en sont la
# traduction clinique typique).
_COMPLICATION_FORTE = re.compile(
    r"(?<!\w)(delirium\w*|\bdt\b|convuls\w*)(?!\w)"
)

# Marqueurs de complication à rattacher à une mention de sevrage proche.
_COMPLICATION = re.compile(r"(?<!\w)(compliqu\w*|complica\w*|difficile)(?!\w)")
_SEVRAGE = re.compile(r"(?<!\w)sevrage\w*(?!\w)")

# Absence explicite d'antécédent de sevrage, ou tout premier sevrage : oriente
# vers False dès lors qu'un sevrage est évoqué sans complication.
_PAS_ANTECEDENT = re.compile(
    r"(?<!\w)((pas|aucun|sans)[^.]{0,6}antecedent[^.]{0,18}sevrage|premier sevrage)"
)

# Proximité (caractères) entre une complication et une mention de sevrage.
_PROXIMITE = 45


@enregistrer("sevrages_compliques")
class ExtracteurSevragesCompliques:
    champ = CHAMPS_PAR_CLE["sevrages_compliques"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        # 1. Complication forte affirmée -> True (haute confiance). Un delirium /
        # DT / des convulsions situés « dans le passé » restent un antécédent
        # compliqué : seule une vraie négation (« pas de delirium ») les écarte,
        # pas un marqueur d'ancienneté.
        for m in _COMPLICATION_FORTE.finditer(texte_normalise):
            if not _negation_explicite(texte_normalise, m.start()):
                return ResultatExtraction(Etat.VRAI, 0.9, _empan(texte_normalise, m))

        # 2. Complication rattachée à un sevrage : affirmée -> True, niée -> False.
        positions_sevrage = [s.start() for s in _SEVRAGE.finditer(texte_normalise)]
        complication_niee = None
        for m in _COMPLICATION.finditer(texte_normalise):
            if not _proche_sevrage(m.start(), positions_sevrage):
                continue
            if est_nie(texte_normalise, m.start(), m.end()):
                complication_niee = m
            else:
                return ResultatExtraction(Etat.VRAI, 0.8, _empan(texte_normalise, m))

        if complication_niee is not None:
            return ResultatExtraction(Etat.FAUX, 0.85, _empan(texte_normalise, complication_niee))

        # 3. Sevrage explicitement absent / premier sevrage -> False.
        m = _PAS_ANTECEDENT.search(texte_normalise)
        if m:
            return ResultatExtraction(Etat.FAUX, 0.85, m.group(0))

        # 4. Pas d'antécédent de sevrage évoqué (ou sevrage actuel seul) -> NA.
        return ResultatExtraction.absent()


# Négation explicite (« pas de », « sans », « aucun », « non », « ni ») dans la
# proposition précédant immédiatement un marqueur — sans les marqueurs
# d'ancienneté, qui ne nient pas un antécédent compliqué.
_NEG_EXPLICITE = re.compile(r"(?<!\w)(pas|sans|aucun|aucune|non|ni)(?!\w)")


def _negation_explicite(texte: str, position: int) -> bool:
    fragment = texte[max(0, position - 30):position]
    coupe = max((fragment.rfind(c) for c in ".;:!?\n)"), default=-1)
    if coupe != -1:
        fragment = fragment[coupe + 1:]
    return bool(_NEG_EXPLICITE.search(fragment))


def _proche_sevrage(position: int, positions_sevrage: list[int]) -> bool:
    return any(abs(position - p) <= _PROXIMITE for p in positions_sevrage)


def _empan(texte: str, m: re.Match, marge: int = 22) -> str:
    debut = max(0, m.start() - marge)
    fin = min(len(texte), m.end() + marge)
    return texte[debut:fin].strip()
