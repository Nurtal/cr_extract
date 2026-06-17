"""Extracteur des troubles anxieux — booléen 3 états.

- ``True``  : anxiété, angoisse, trouble anxieux, attaque / trouble panique,
  syndrome anxio-dépressif.
- ``False`` : explicitement écarté (« pas de trouble anxieux », « pas
  d'anxiété »).
- ``NA``    : non abordé.

« anxiolytique » (médicament) n'est pas retenu comme trouble anxieux — de même
que « antidépresseur » ne valait pas dépression.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

# « anxiolytique » est volontairement absent (médicament, pas un trouble).
_ANXIEUX = re.compile(
    r"(?<!\w)("
    r"anxiete\w*|anxieux|anxieuse|angoiss\w*|trouble\w* anxieux|"
    r"attaque\w* de panique|trouble\w* panique|anxio-depress\w*"
    r")(?!\w)"
)


@enregistrer("troubles_anxieux")
class ExtracteurTroublesAnxieux:
    champ = CHAMPS_PAR_CLE["troubles_anxieux"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_ANXIEUX.finditer(texte_normalise))
        affirmees = [
            m for m in occurrences
            if not est_nie(texte_normalise, m.start(), m.end())
        ]
        if affirmees:
            return ResultatExtraction(Etat.VRAI, 0.9, affirmees[0].group(0))
        if occurrences:  # mention présente mais niée
            return ResultatExtraction(Etat.FAUX, 0.9, occurrences[0].group(0))
        return ResultatExtraction.absent()
