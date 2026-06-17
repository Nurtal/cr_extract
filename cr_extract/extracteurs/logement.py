"""Extracteur SDF / absence de logement (#3) — booléen 3 états.

- ``True`` : SDF, sans domicile fixe, à la rue, dort dehors, pas de logement…
- ``NA`` : information non documentée (notes d'urgence sans état civil,
  hébergement « non précisé » / « à organiser » / « temporaire »).
- ``False`` (défaut) : patient présumé logé — y compris implicitement lorsque le
  CR décrit une insertion sociale sans mention d'absence de logement.

Le ``False`` par défaut traduit la convention observée dans la vérité terrain :
un compte rendu « ordinaire » sans signal de précarité suppose un logement.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.extracteurs import enregistrer

_SDF = re.compile(
    r"(?<!\w)(sdf|sans domicile|sans abri|sans logement|pas de logement|"
    r"a la rue|dort dehors|dort dans la rue|vivant a la rue|en rupture d'hebergement)"
)

# Signaux d'absence d'information : logement non documenté ou hébergement
# précaire/transitoire que la vérité terrain laisse en NA. On y inclut les
# notes-souches de transmission (« aucune conso d'aucune sorte »), dépourvues de
# toute évaluation sociale — distinctes d'une négation ciblée (« aucune
# consommation d'alcool »).
_NA = re.compile(
    r"(?<!\w)(logement non\w*|hebergement non\w*|hebergement a organiser|"
    r"non document\w*|non renseign\w*|non precis\w*|"
    r"temporairement|de maniere precaire|"
    r"pas d'info\w*|aucune information|impossible d'obtenir|rien de renseign\w*|"
    r"foyer pour jeunes travailleurs|d'aucune sorte|aucune conso(?!mmation))"
)


@enregistrer("sdf")
class ExtracteurSdf:
    champ = CHAMPS_PAR_CLE["sdf"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        sdf = _SDF.search(texte_normalise)
        if sdf:
            return ResultatExtraction(Etat.VRAI, 0.9, sdf.group(0))
        if _NA.search(texte_normalise):
            return ResultatExtraction.absent()
        # Aucun signal de précarité : logement présumé (convention de la vérité
        # terrain). Confiance modérée car la décision est implicite.
        return ResultatExtraction(Etat.FAUX, 0.6, None)
