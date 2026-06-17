"""Extracteur de la situation conjugale (#1).

Catégoriel : ``en couple`` / ``célibataire`` / ``NA``.

- ``en couple`` : marié·e, en couple, conjoint, compagne/compagnon, concubinage…
- ``célibataire`` : célibataire, divorcé·e, séparé·e, veuf/veuve, vit seul·e.
- ``NA`` : situation non renseignée (notes d'urgence sans état civil).

L'« en couple » prime sur le « seul » résiduel ; les marqueurs de rupture
(divorcé, veuf…) signifient ``célibataire`` au moment du CR.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, ResultatExtraction
from cr_extract.extracteurs import enregistrer

_EN_COUPLE = re.compile(
    r"(?<!\w)(en couple|marie|mariee|son conjoint|sa conjointe|"
    r"compagne|compagnon|concubin\w*|pacse\w*|vit avec son|vit avec sa)(?!\w)"
)
_CELIBATAIRE = re.compile(
    r"(?<!\w)(celibataire|celib|divorce|divorcee|separe|separee|"
    r"veuf|veuve|vit seul|vit seule|vivant seul\w*)(?!\w)"
)


@enregistrer("situation_conjugale")
class ExtracteurSituationConjugale:
    champ = CHAMPS_PAR_CLE["situation_conjugale"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        couple = _EN_COUPLE.search(texte_normalise)
        celib = _CELIBATAIRE.search(texte_normalise)
        if couple and not celib:
            return ResultatExtraction("en couple", 1.0, couple.group(0))
        if celib and not couple:
            return ResultatExtraction("célibataire", 1.0, celib.group(0))
        if couple and celib:
            # Cooccurrence rare (« divorcé donc célibataire ») : un marqueur de
            # rupture explicite tranche pour célibataire.
            if re.search(r"(?<!\w)(divorce|separe|veuf|veuve)", texte_normalise):
                return ResultatExtraction("célibataire", 0.7, celib.group(0))
            return ResultatExtraction("en couple", 0.7, couple.group(0))
        return ResultatExtraction.absent()
