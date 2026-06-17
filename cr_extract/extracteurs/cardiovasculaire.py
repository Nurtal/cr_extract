"""Extracteur des problèmes cardiovasculaires — booléen 3 états.

- ``True``  : pathologie / événement cardiovasculaire établi — AVC, infarctus /
  IDM, insuffisance cardiaque, endocardite, coronaropathie, cardiopathie, angor,
  HTA, artériopathie, embolie pulmonaire, phlébite / TVP, trouble du rythme,
  fibrillation, antécédents cardiovasculaires…
- ``False`` : explicitement écarté (« pas d'antécédent cardiovasculaire »,
  « pas de cardiopathie »).
- ``NA``    : non abordé.

Choix de modélisation : on ne retient **pas** les symptômes isolés (palpitations,
tachycardie post-stimulant, douleur thoracique) ni les simples bilans
(« évaluation / bilan cardiovasculaire »), qui ne traduisent pas une pathologie
CV avérée dans ce corpus.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

_CARDIOVASCULAIRE = re.compile(
    r"(?<!\w)("
    r"\bavc\b|infarctus|\bidm\b|insuffisance cardiaque|endocardit\w*|"
    r"coronaropath\w*|coronarien\w*|cardiopath\w*|angor|angine de poitrine|"
    r"\bhta\b|hypertension arterielle|arteriopath\w*|embolie pulmonaire|"
    r"phlebit\w*|thrombose veineuse|\btvp\b|\bsca\b|trouble\w* du rythme|"
    r"fibrillation\w*|antecedents? cardiovasculaire\w*|antecedents? cardiaque\w*"
    r")(?!\w)"
)


@enregistrer("cardiovasculaire")
class ExtracteurCardiovasculaire:
    champ = CHAMPS_PAR_CLE["cardiovasculaire"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_CARDIOVASCULAIRE.finditer(texte_normalise))
        affirmees = [
            m for m in occurrences
            if not est_nie(texte_normalise, m.start(), m.end())
        ]
        if affirmees:
            return ResultatExtraction(Etat.VRAI, 0.9, affirmees[0].group(0))
        if occurrences:  # mention présente mais niée
            return ResultatExtraction(Etat.FAUX, 0.9, occurrences[0].group(0))
        return ResultatExtraction.absent()
