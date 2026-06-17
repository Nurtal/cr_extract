"""Extracteur des troubles cognitifs — booléen 3 états.

- ``True``  : trouble cognitif établi — troubles cognitifs / mnésiques, déficit /
  altération cognitive, démence, syndrome de Korsakoff, encéphalopathie de
  Wernicke.
- ``False`` : explicitement écarté (« pas de troubles cognitifs », « fonctions
  cognitives normales »).
- ``NA``    : non abordé.

Pièges évités :

- « risques cognitifs » (information délivrée, p. ex. sur la kétamine) n'est pas
  un trouble avéré -> on n'attrape pas « cognitif » seul, mais « troubles /
  déficit … cognitif » ;
- « syndrome confusionnel » / « désorientation » isolés (états aigus / symptômes)
  ne sont pas retenus comme trouble cognitif chronique.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

_COGNITIF = re.compile(
    r"(?<!\w)("
    r"troubles? cognitif\w*|deficit\w* cognitif\w*|deficience\w* cognitive\w*|"
    r"alteration\w* cognitive\w*|deterioration cognitive|atteinte cognitive|"
    r"troubles? mnesiques?|troubles? de la memoire|"
    r"demence\w*|dement\w*|korsakoff|encephalopathie de wernicke|wernicke"
    r")(?!\w)"
)

# Énoncés de normalité cognitive (sans terme de trouble) -> False.
_NIEE = re.compile(
    r"(?<!\w)(fonctions cognitives normales|cognition normale|"
    r"examen cognitif normal|sans trouble\w* cognitif\w*)"
)


@enregistrer("troubles_cognitifs")
class ExtracteurTroublesCognitifs:
    champ = CHAMPS_PAR_CLE["troubles_cognitifs"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_COGNITIF.finditer(texte_normalise))
        affirmees = [
            m for m in occurrences
            if not est_nie(texte_normalise, m.start(), m.end())
        ]
        if affirmees:
            return ResultatExtraction(Etat.VRAI, 0.9, affirmees[0].group(0))
        nie = _NIEE.search(texte_normalise)
        if nie or occurrences:
            preuve = nie.group(0) if nie else occurrences[0].group(0)
            return ResultatExtraction(Etat.FAUX, 0.9, preuve)
        return ResultatExtraction.absent()
