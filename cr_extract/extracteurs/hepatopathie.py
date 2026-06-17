"""Extracteur de l'hépatopathie (atteinte hépatique) — booléen 3 états.

- ``True``  : maladie du foie — cirrhose, hépatite, hépatopathie, cytolyse,
  stéatose, fibrose, insuffisance hépatique, varices œsophagiennes (signe
  d'hypertension portale), encéphalopathie hépatique, CHC, VHC/VHB…
- ``False`` : atteinte hépatique explicitement écartée — « foie normal »,
  « bilan hépatique normal », « pas de cirrhose », « transaminases normales ».
- ``NA``    : non abordé.

Pièges évités : « bilan hépatique » / « fonction hépatique » seuls (examen, pas
maladie) ne déclenchent pas ``True`` ; on ne s'appuie donc pas sur « hépatique »
isolé mais sur des entités pathologiques explicites.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

# Entités d'atteinte hépatique. « varices \w*sophag… » couvre « œsophagiennes »
# (le « œ » est conservé par la normalisation, \w le capture).
_HEPATOPATHIE = re.compile(
    r"(?<!\w)("
    r"hepatopathie\w*|cirrhos\w*|cirrhotiqu\w*|hepatite\w*|cytolyse|"
    r"steatos\w*|fibrose hepatiqu\w*|insuffisance hepat\w*|"
    r"hypertension portale|encephalopathie hepatiqu\w*|hepatomegalie|"
    r"hepatocarcinome|carcinome hepatocellulaire|\bchc\b|"
    r"varices\s+\w*sophag\w*|\bvhc\b|\bvhb\b"
    r")(?!\w)"
)

# Négation explicite d'atteinte hépatique (formules sans terme pathologique).
_NIEE = re.compile(
    r"(?<!\w)(foie normal|bilan hepatique normal|fonction hepatique normale|"
    r"transaminases normales|bilan hepatique sans particularite)"
)


@enregistrer("hepatopathie")
class ExtracteurHepatopathie:
    champ = CHAMPS_PAR_CLE["hepatopathie"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        occurrences = list(_HEPATOPATHIE.finditer(texte_normalise))
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
