"""Extracteur des tentatives de suicide — booléen 3 états.

- ``True``  : tentative de suicide / d'autolyse, autolyse, geste suicidaire /
  auto-agressif, intoxication médicamenteuse volontaire (IMV), passage à l'acte
  suicidaire, défenestration, pendaison, « TS ».
- ``False`` : explicitement écarté (« pas de tentative de suicide »).
- ``NA``    : non abordé.

Distinction clé : on ne retient que les **passages à l'acte**, pas l'idéation
(« idées noires », « idées suicidaires » -> NA). On exige aussi le contexte
suicidaire explicite, car « tentative » seul peut viser un sevrage (« troisième
tentative ») et « geste » un acte technique (« geste endoscopique »).
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

_TENTATIVE = re.compile(
    r"(?<!\w)("
    r"tentative\w* de suicide|tentative\w* d'autolyse|tentative\w* de mettre fin|"
    r"geste\w* suicidaire|geste\w* auto-?agressif|autolyse|"
    r"intoxication medicamenteuse volontaire|intoxication volontaire|\bimv\b|"
    r"passage a l'acte suicidaire|\bts\b|defenestration|pendaison"
    r")(?!\w)"
)


@enregistrer("tentative_suicide")
class ExtracteurTentativeSuicide:
    champ = CHAMPS_PAR_CLE["tentative_suicide"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_TENTATIVE.finditer(texte_normalise))
        affirmees = [
            m for m in occurrences
            if not est_nie(texte_normalise, m.start(), m.end())
        ]
        if affirmees:
            return ResultatExtraction(Etat.VRAI, 0.9, affirmees[0].group(0))
        if occurrences:  # mention présente mais niée (« pas de tentative de suicide »)
            return ResultatExtraction(Etat.FAUX, 0.9, occurrences[0].group(0))
        return ResultatExtraction.absent()
