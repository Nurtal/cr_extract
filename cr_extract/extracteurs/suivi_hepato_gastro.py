"""Extracteur du suivi en hépato-gastro-entérologie (HGE) — booléen 3 états.

- ``True``  : le patient est suivi / orienté en hépato-gastro-entérologie
  (compte rendu HGE, consultation/avis d'un gastro-entérologue ou hépatologue,
  « suivi HGE »…).
- ``False`` : suivi HGE explicitement écarté (« pas de suivi gastro-entérologique »).
- ``NA``    : non abordé.

Piège évité : « chirurgie digestive » / « hémorragie digestive » désignent un
acte ou un symptôme, **pas** un suivi HGE — le terme « digestive » est donc
volontairement exclu. On s'appuie sur la spécialité (hépato-gastro-entérologie,
gastro-entérologue, hépatologue, HGE).
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

# Spécialité hépato-gastro-entérologie sous ses différentes formes.
_HGE = re.compile(
    r"(?<!\w)("
    r"hepato[- ]?gastro\w*|gastro[- ]?enterolog\w*|hepatolog\w*|\bhge\b"
    r")(?!\w)"
)


@enregistrer("suivi_hepato_gastro")
class ExtracteurSuiviHepatoGastro:
    champ = CHAMPS_PAR_CLE["suivi_hepato_gastro"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_HGE.finditer(texte_normalise))
        affirmees = [
            m for m in occurrences
            if not est_nie(texte_normalise, m.start(), m.end())
        ]
        if affirmees:
            return ResultatExtraction(Etat.VRAI, 0.9, affirmees[0].group(0))
        if occurrences:  # mention présente mais niée (« pas de suivi gastro »)
            return ResultatExtraction(Etat.FAUX, 0.9, occurrences[0].group(0))
        return ResultatExtraction.absent()
