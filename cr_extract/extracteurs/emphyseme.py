"""Extracteur de l'emphysème — booléen 3 états.

- ``True``  : emphysème (pulmonaire), poumons emphysémateux.
- ``False`` : explicitement écarté (« pas d'emphysème »).
- ``NA``    : non abordé.

L'emphysème étant une composante de la BPCO, ce champ recoupe volontairement
``bpco`` : « emphysème pulmonaire » active les deux (axes distincts mais liés).
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

_EMPHYSEME = re.compile(r"(?<!\w)(emphysem\w*)(?!\w)")


@enregistrer("emphyseme")
class ExtracteurEmphyseme:
    champ = CHAMPS_PAR_CLE["emphyseme"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_EMPHYSEME.finditer(texte_normalise))
        affirmees = [
            m for m in occurrences
            if not est_nie(texte_normalise, m.start(), m.end())
        ]
        if affirmees:
            return ResultatExtraction(Etat.VRAI, 0.9, affirmees[0].group(0))
        if occurrences:  # mention présente mais niée (« pas d'emphysème »)
            return ResultatExtraction(Etat.FAUX, 0.9, occurrences[0].group(0))
        return ResultatExtraction.absent()
