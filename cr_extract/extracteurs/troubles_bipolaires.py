"""Extracteur des troubles bipolaires — booléen 3 états.

- ``True``  : trouble bipolaire, bipolarité, épisode / accès / état maniaque,
  hypomanie, psychose maniaco-dépressive, cyclothymie.
- ``False`` : explicitement écarté (« pas de trouble bipolaire »).
- ``NA``    : non abordé.

On évite « manie » au sens courant (manie = habitude/lubie) et l'abréviation
« TB » (tuberculose) ; on s'appuie sur les entités explicitement bipolaires /
maniaques. La « décompensation thymique » (humeur, non spécifiquement bipolaire)
n'est pas retenue.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

_BIPOLAIRE = re.compile(
    r"(?<!\w)("
    r"bipolair\w*|bipolarit\w*|maniaque\w*|maniaco-?depress\w*|hypomani\w*|"
    r"episode maniaque|acces maniaque|etat maniaque|phase maniaque|"
    r"cyclothym\w*|\bpmd\b"
    r")(?!\w)"
)


@enregistrer("troubles_bipolaires")
class ExtracteurTroublesBipolaires:
    champ = CHAMPS_PAR_CLE["troubles_bipolaires"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_BIPOLAIRE.finditer(texte_normalise))
        affirmees = [
            m for m in occurrences
            if not est_nie(texte_normalise, m.start(), m.end())
        ]
        if affirmees:
            return ResultatExtraction(Etat.VRAI, 0.9, affirmees[0].group(0))
        if occurrences:  # mention présente mais niée (« pas de trouble bipolaire »)
            return ResultatExtraction(Etat.FAUX, 0.9, occurrences[0].group(0))
        return ResultatExtraction.absent()
