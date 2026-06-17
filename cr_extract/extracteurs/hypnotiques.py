"""Extracteurs des hypnotiques : prise et type (molécule).

- ``hypnotiques`` (booléen 3 états) : prise d'un hypnotique / somnifère.
  ``True`` si affirmée, ``False`` si niée, ``NA`` si non abordée.
- ``hypnotique_type`` (catégoriel) : molécule (DCI) si elle est nommée, sinon
  ``NA``.

Contrairement aux benzodiazépines (où une prescription de sevrage est exclue),
on compte ici toute **prise** d'hypnotique — qu'elle soit prescrite (insomnie)
ou détournée — car le champ porte sur la consommation du produit.

Recoupement assumé avec les benzodiazépines : les « Z-drugs » (zolpidem,
zopiclone) et certaines benzodiazépines hypnotiques (nitrazépam, témazépam…)
relèvent des deux axes.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie, evaluer_terme
from cr_extract.extracteurs import enregistrer

# Molécules hypnotiques (DCI canonique -> motif DCI + noms commerciaux).
_MOLECULES: tuple[tuple[str, str], ...] = (
    ("zolpidem", r"zolpidem|stilnox"),
    ("zopiclone", r"zopiclone|imovane"),
    ("nitrazepam", r"nitrazepam"),
    ("temazepam", r"temazepam|normison"),
    ("lormetazepam", r"lormetazepam|noctamide"),
    ("loprazolam", r"loprazolam|havlane"),
    ("estazolam", r"estazolam|nuctalon"),
    ("flunitrazepam", r"flunitrazepam|rohypnol"),
    ("doxylamine", r"doxylamine|donormyl"),
    ("melatonine", r"melatonine|circadin"),
)

# Termes génériques de classe.
_GENERIQUE = r"hypnotique\w*|somnifere\w*"

# Motif global (présence) : générique OU une molécule/nom commercial.
_HYPNOTIQUE = re.compile(
    r"(?<!\w)(" + _GENERIQUE + r"|" + r"|".join(m for _, m in _MOLECULES) + r")(?!\w)"
)
_MOLECULES_COMPILES = tuple(
    (dci, re.compile(rf"(?<!\w)({motif})(?!\w)")) for dci, motif in _MOLECULES
)


@enregistrer("hypnotiques")
class ExtracteurHypnotiques:
    champ = CHAMPS_PAR_CLE["hypnotiques"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        decision = evaluer_terme(texte_normalise, _HYPNOTIQUE)
        if decision.valeur == "present":
            return ResultatExtraction(Etat.VRAI, 0.9, decision.preuve)
        if decision.valeur == "nie":
            return ResultatExtraction(Etat.FAUX, 0.9, decision.preuve)
        return ResultatExtraction.absent()


@enregistrer("hypnotique_type")
class ExtracteurHypnotiqueType:
    champ = CHAMPS_PAR_CLE["hypnotique_type"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        # Le type n'a de sens que si une prise d'hypnotique est avérée.
        if evaluer_terme(texte_normalise, _HYPNOTIQUE).valeur != "present":
            return ResultatExtraction.absent()
        # Première molécule nommée et affirmée.
        for dci, motif in _MOLECULES_COMPILES:
            m = motif.search(texte_normalise)
            if m and not est_nie(texte_normalise, m.start(), m.end()):
                return ResultatExtraction(dci, 0.9, m.group(0))
        # Mention générique (« somnifère ») sans molécule précisée.
        return ResultatExtraction.absent()
