"""Extracteur de la BPCO (bronchopneumopathie chronique obstructive) — 3 états.

- ``True``  : BPCO, bronchite chronique (obstructive), emphysème.
- ``False`` : explicitement écartée (« pas de BPCO », « EFR normales, pas de
  BPCO »).
- ``NA``    : non abordé.

Piège évité : « pneumopathie » (pneumonie aiguë) et « respiratoire » seuls ne
sont **pas** une BPCO — on cible l'entité chronique obstructive.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

_BPCO = re.compile(
    r"(?<!\w)("
    r"\bbpco\b|broncho-?pneumopathie chronique\w*|bronchite chronique|emphysem\w*"
    r")(?!\w)"
)


@enregistrer("bpco")
class ExtracteurBpco:
    champ = CHAMPS_PAR_CLE["bpco"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_BPCO.finditer(texte_normalise))
        affirmees = [
            m for m in occurrences
            if not est_nie(texte_normalise, m.start(), m.end())
        ]
        if affirmees:
            return ResultatExtraction(Etat.VRAI, 0.9, affirmees[0].group(0))
        if occurrences:  # mention présente mais niée (« pas de BPCO »)
            return ResultatExtraction(Etat.FAUX, 0.9, occurrences[0].group(0))
        return ResultatExtraction.absent()
