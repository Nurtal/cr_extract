"""Extracteur du diabète — booléen 3 états.

- ``True``  : diabète (type 1 / 2), diabétique, DID / DNID, insulinodépendant.
- ``False`` : explicitement écarté (« pas de diabète », « non diabétique »).
- ``NA``    : non abordé.

On ne s'appuie pas sur « glycémie » / « hyperglycémie » seuls (valeur de
laboratoire, pas nécessairement un diabète).
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

_DIABETE = re.compile(
    r"(?<!\w)("
    r"diabet\w*|\bdid\b|\bdnid\b|insulino[- ]?dependant\w*|insulino[- ]?requerant\w*"
    r")(?!\w)"
)


@enregistrer("diabete")
class ExtracteurDiabete:
    champ = CHAMPS_PAR_CLE["diabete"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_DIABETE.finditer(texte_normalise))
        affirmees = [
            m for m in occurrences
            if not est_nie(texte_normalise, m.start(), m.end())
        ]
        if affirmees:
            return ResultatExtraction(Etat.VRAI, 0.9, affirmees[0].group(0))
        if occurrences:  # mention présente mais niée (« pas de diabète »)
            return ResultatExtraction(Etat.FAUX, 0.9, occurrences[0].group(0))
        return ResultatExtraction.absent()
