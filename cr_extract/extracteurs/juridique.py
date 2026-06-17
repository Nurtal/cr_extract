"""Extracteur de la mesure de protection juridique (#4).

Champ catégoriel simple : ``curatelle`` / ``tutelle`` / ``NA``. La « sauvegarde
de justice » n'est pas une valeur du catalogue et reste donc ``NA``.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

_CURATELLE = re.compile(r"(?<!\w)curatelle\w*(?!\w)")
_TUTELLE = re.compile(r"(?<!\w)tutelle\w*(?!\w)")


@enregistrer("protection_juridique")
class ExtracteurProtectionJuridique:
    champ = CHAMPS_PAR_CLE["protection_juridique"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        for motif, valeur in ((_CURATELLE, "curatelle"), (_TUTELLE, "tutelle")):
            m = motif.search(texte_normalise)
            # « pas de mesure de protection » : le terme curatelle/tutelle n'est
            # alors pas censé apparaître, mais on filtre une éventuelle négation.
            if m and not est_nie(texte_normalise, m.start(), m.end()):
                return ResultatExtraction(valeur, 1.0, m.group(0))
        return ResultatExtraction.absent()
