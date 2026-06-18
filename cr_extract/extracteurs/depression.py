"""Extracteur de la dépression / épisode dépressif — booléen 3 états.

- ``True``  : épisode dépressif, dépression, syndrome / état / trouble dépressif,
  syndrome anxio-dépressif, EDM.
- ``False`` : explicitement écarté (« pas de syndrome dépressif »).
- ``NA``    : non abordé.

Choix de modélisation : l'**anxiété / angoisse** isolée et la « décompensation
thymique » (humeur, non spécifiquement dépressive) ne sont pas comptées ; les
« idées noires » (symptôme) ne suffisent pas non plus. On cible la mention
dépressive explicite.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

# « depress\w* » couvre dépression / dépressif / dépressive, y compris dans
# « anxio-dépressif » ; « antidépresseur » est exclu (préfixe « anti »).
# « EDM » (épisode dépressif majeur) et « EDC » (épisode dépressif caractérisé,
# terminologie actuelle) sont les abréviations consacrées.
_DEPRESSION = re.compile(r"(?<!\w)(depress\w*|anxio-depress\w*|\bedm\b|\bedc\b)(?!\w)")


@enregistrer("depression")
class ExtracteurDepression:
    champ = CHAMPS_PAR_CLE["depression"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_DEPRESSION.finditer(texte_normalise))
        affirmees = [
            m for m in occurrences
            if not est_nie(texte_normalise, m.start(), m.end())
        ]
        if affirmees:
            return ResultatExtraction(Etat.VRAI, 0.9, affirmees[0].group(0))
        if occurrences:  # mention présente mais niée (« pas de syndrome dépressif »)
            return ResultatExtraction(Etat.FAUX, 0.9, occurrences[0].group(0))
        return ResultatExtraction.absent()
