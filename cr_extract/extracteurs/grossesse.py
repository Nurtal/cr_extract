"""Extracteur du statut de grossesse (booléen 3 états).

- ``True``  : grossesse **en cours** (« enceinte », « enceinte de 18 SA »,
  « grossesse évolutive »…).
- ``False`` : grossesse explicitement écartée (« pas enceinte », « test de
  grossesse négatif »).
- ``NA``    : non abordé.

Point délicat : on s'appuie sur « enceinte » / un contexte de grossesse *en
cours*, et **non** sur le mot « grossesse » seul, qui apparaît aussi pour des
antécédents (« deux grossesses antérieures »), un projet (« désir de grossesse »)
ou un repère temporel (« sevrage tabac avant grossesse ») — autant de cas qui ne
signifient pas une grossesse actuelle (-> ``NA``).
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

# Marqueurs d'une grossesse en cours.
_PRESENTE = re.compile(
    r"(?<!\w)(enceinte|gestante|grossesse en cours|grossesse evolutive|"
    r"grossesse de \d+|\d+\s*semaines d'amenorrhee|\d+\s*sa)(?!\w)"
)

# Négation explicite d'une grossesse.
_NIEE = re.compile(
    r"(?<!\w)(pas enceinte|non enceinte|pas de grossesse|absence de grossesse|"
    r"grossesse exclue|test de grossesse negatif|beta-?hcg negati\w*|hcg negati\w*)"
)


@enregistrer("grossesse")
class ExtracteurGrossesse:
    champ = CHAMPS_PAR_CLE["grossesse"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_PRESENTE.finditer(texte_normalise))
        affirmees = [
            m for m in occurrences
            if not est_nie(texte_normalise, m.start(), m.end())
        ]
        if affirmees:
            return ResultatExtraction(Etat.VRAI, 0.9, affirmees[0].group(0))
        # Négation explicite, ou « enceinte » nié (« pas enceinte ») -> False.
        nie = _NIEE.search(texte_normalise)
        if nie or occurrences:
            preuve = nie.group(0) if nie else occurrences[0].group(0)
            return ResultatExtraction(Etat.FAUX, 0.9, preuve)
        return ResultatExtraction.absent()
