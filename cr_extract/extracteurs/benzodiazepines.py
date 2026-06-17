"""Extracteurs des benzodiazépines : présence et type (molécule).

- ``benzodiazepines`` (booléen 3 états) : usage/mésusage de benzodiazépines (ou
  apparentés « Z », zolpidem/zopiclone). ``True`` si consommation affirmée,
  ``False`` si niée, ``NA`` si non abordé.
- ``benzodiazepine_type`` (catégoriel) : molécule (DCI) si elle est nommée, sinon
  ``NA``.

Distinction importante : une benzodiazépine **prescrite en traitement** (« sevrage
sous oxazépam dégressif », « couverture par diazépam ») n'est pas une
consommation au sens addictologique — ce contexte thérapeutique est filtré et ne
déclenche pas ``True``.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie
from cr_extract.extracteurs import enregistrer

# --------------------------------------------------------------------------- #
# Molécules (DCI canonique -> motif DCI + noms commerciaux courants)
# --------------------------------------------------------------------------- #
_MOLECULES: tuple[tuple[str, str], ...] = (
    ("alprazolam", r"alprazolam|xanax"),
    ("bromazepam", r"bromazepam|lexomil"),
    ("clobazam", r"clobazam|urbanyl"),
    ("clonazepam", r"clonazepam|rivotril"),
    ("clorazepate", r"clorazepate|tranxene"),
    ("diazepam", r"diazepam|valium"),
    ("flunitrazepam", r"flunitrazepam|rohypnol"),
    ("lorazepam", r"lorazepam|temesta"),
    ("lormetazepam", r"lormetazepam|noctamide"),
    ("midazolam", r"midazolam"),
    ("nitrazepam", r"nitrazepam"),
    ("oxazepam", r"oxazepam|seresta"),
    ("prazepam", r"prazepam|lysanxia"),
    ("temazepam", r"temazepam|normison"),
    ("zolpidem", r"zolpidem|stilnox"),       # apparenté (« Z-drug »)
    ("zopiclone", r"zopiclone|imovane"),     # apparenté (« Z-drug »)
)

# Termes génériques de classe.
_GENERIQUE = r"benzodiazepin\w*|\bbenzos?\b|\bbzd\b"

# Motif global (présence) : générique OU une molécule/nom commercial.
_BENZO = re.compile(
    r"(?<!\w)(" + _GENERIQUE + r"|" + r"|".join(m for _, m in _MOLECULES) + r")(?!\w)"
)
_MOLECULES_COMPILES = tuple(
    (dci, re.compile(rf"(?<!\w)({motif})(?!\w)")) for dci, motif in _MOLECULES
)

# --------------------------------------------------------------------------- #
# Contexte thérapeutique vs mésusage
# --------------------------------------------------------------------------- #
# Indices d'une prescription/traitement (avant la molécule, ou « dégressif » après).
_THERAP_AVANT = re.compile(
    r"(sevrage sous|(?<!\w)sous(?!\w)|traitement|(?<!\w)ttt(?!\w)|prescri\w*|"
    r"couverture par|relais par|instauration|perfusion|introduction de)"
)
_THERAP_APRES = re.compile(r"degressi\w*")
# Indices de consommation/mésusage qui priment sur un éventuel contexte « sous ».
_MESUSAGE = re.compile(
    r"(dependance|mesusage|abus|addiction|consommation|usage|quotidien|"
    r"recreati\w*|detourne\w*)"
)


def _therapeutique(texte: str, debut: int, fin: int) -> bool:
    """Vrai si l'occurrence relève d'un usage thérapeutique (et non d'un mésusage)."""
    avant = texte[max(0, debut - 30):debut]
    apres = texte[fin:fin + 18]
    if not (_THERAP_AVANT.search(avant) or _THERAP_APRES.search(apres)):
        return False
    fenetre = texte[max(0, debut - 30):fin + 18]
    return not _MESUSAGE.search(fenetre)


def _presence(texte_normalise: str):
    """Décision de présence : ``("present"|"nie", empan)`` ou ``(None, None)``.

    Une occupation affirmée et non thérapeutique l'emporte ; à défaut une
    occurrence niée donne ``"nie"`` ; les occurrences purement thérapeutiques
    sont ignorées.
    """
    niee = None
    for m in _BENZO.finditer(texte_normalise):
        if est_nie(texte_normalise, m.start(), m.end()):
            niee = niee or m
            continue
        if _therapeutique(texte_normalise, m.start(), m.end()):
            continue
        return "present", m.group(0)
    if niee is not None:
        return "nie", niee.group(0)
    return None, None


@enregistrer("benzodiazepines")
class ExtracteurBenzodiazepines:
    champ = CHAMPS_PAR_CLE["benzodiazepines"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        decision, empan = _presence(texte_normalise)
        if decision == "present":
            return ResultatExtraction(Etat.VRAI, 0.9, empan)
        if decision == "nie":
            return ResultatExtraction(Etat.FAUX, 0.9, empan)
        return ResultatExtraction.absent()


@enregistrer("benzodiazepine_type")
class ExtracteurBenzodiazepineType:
    champ = CHAMPS_PAR_CLE["benzodiazepine_type"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        # Le type n'a de sens que si une consommation de benzodiazépine est avérée.
        if _presence(texte_normalise)[0] != "present":
            return ResultatExtraction.absent()
        # Première molécule nommée et affirmée.
        for dci, motif in _MOLECULES_COMPILES:
            m = motif.search(texte_normalise)
            if m and not est_nie(texte_normalise, m.start(), m.end()):
                return ResultatExtraction(dci, 0.9, m.group(0))
        # Mention générique sans molécule précisée.
        return ResultatExtraction.absent()
