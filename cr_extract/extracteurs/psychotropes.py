"""Extracteur de l'utilisation de psychotropes (médicaments) — booléen 3 états.

- ``True``  : prise d'un médicament psychotrope — psychotrope (générique),
  antidépresseur, neuroleptique / antipsychotique, anxiolytique,
  thymorégulateur / normothymique, lithium.
- ``False`` : explicitement écarté (« pas de psychotrope », « aucun traitement
  psychotrope »).
- ``NA``    : non abordé.

Ce champ est le foyer naturel des mentions « antidépresseur » / « anxiolytique »,
volontairement exclues des diagnostics (`depression`, `troubles_anxieux`) où
elles désignaient un traitement et non la pathologie.

Les benzodiazépines et hypnotiques, qui ont leurs propres champs, ne sont pas
re-captés ici (sauf mention explicite du mot « psychotrope »).
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

_PSYCHOTROPES = re.compile(
    r"(?<!\w)("
    r"psychotrop\w*|antidepress\w*|neurolep\w*|antipsychot\w*|anxiolyt\w*|"
    r"thymoregul\w*|thymo-regul\w*|normothym\w*|regulateur\w* de l'humeur|lithium|"
    r"\bnl\b"  # NL = neuroleptique (abréviation courante en psychiatrie)
    r")(?!\w)"
)


@enregistrer("psychotropes")
class ExtracteurPsychotropes:
    champ = CHAMPS_PAR_CLE["psychotropes"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_PSYCHOTROPES.finditer(texte_normalise))
        affirmees = [
            m for m in occurrences
            if not est_nie(texte_normalise, m.start(), m.end())
        ]
        if affirmees:
            return ResultatExtraction(Etat.VRAI, 0.9, affirmees[0].group(0))
        if occurrences:  # mention présente mais niée (« pas de psychotrope »)
            return ResultatExtraction(Etat.FAUX, 0.9, occurrences[0].group(0))
        return ResultatExtraction.absent()
