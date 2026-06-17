"""Extracteur de la pancréatite — booléen 3 états.

- ``True``  : pancréatite (aiguë / chronique / éthylique), pancréatopathie.
- ``False`` : pancréatite explicitement écartée (« pas de pancréatite »,
  « lipase normale, pas de pancréatite »).
- ``NA``    : non abordé.

On cible l'entité « pancréatite » elle-même, pas « pancréas » / « pancréatique »
seuls (qui peuvent désigner un organe ou un autre contexte).
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

_PANCREATITE = re.compile(r"(?<!\w)(pancreatit\w*|pancreatopathie\w*)(?!\w)")


@enregistrer("pancreatite")
class ExtracteurPancreatite:
    champ = CHAMPS_PAR_CLE["pancreatite"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_PANCREATITE.finditer(texte_normalise))
        affirmees = [
            m for m in occurrences
            if not est_nie(texte_normalise, m.start(), m.end())
        ]
        if affirmees:
            return ResultatExtraction(Etat.VRAI, 0.9, affirmees[0].group(0))
        if occurrences:  # mention présente mais niée (« pas de pancréatite »)
            return ResultatExtraction(Etat.FAUX, 0.9, occurrences[0].group(0))
        return ResultatExtraction.absent()
