"""Extracteurs du traitement de substitution aux opiacés (TSO) et de son type.

- ``traitement_substitution`` (booléen 3 états) : le patient est-il sous TSO ?
  ``True`` si affirmé, ``False`` si nié, ``NA`` si non abordé.
- ``traitement_substitution_type`` (catégoriel) : ``methadone`` / ``buprenorphine``
  si la molécule est nommée, sinon ``NA``.

Le TSO est un sous-ensemble *opiacé* des addictolytiques : il ne couvre que la
méthadone et la buprénorphine (et leurs noms commerciaux). La substitution
**nicotinique** (tabac) en est explicitement exclue.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie_explicite
from cr_extract.extracteurs import enregistrer

# Molécules de substitution opiacée (DCI canonique -> motif DCI + noms commerciaux).
_MOLECULES: tuple[tuple[str, str], ...] = (
    ("methadone", r"methadone|metha"),
    ("buprenorphine", r"buprenorphine|subutex|suboxone|\bbhd\b"),
)

# Termes génériques de TSO (sans molécule précise). La substitution nicotinique
# est écartée par une anti-correspondance explicite.
_GENERIQUE = (
    r"(?:traitement|ttt)\s+(?:de\s+)?substitution(?!\w*\s+nicotin)|"
    r"substitution aux opiaces|substitution opiac\w*|\btso\b|"
    r"sous substitution(?!\w*\s+nicotin)|substitue\w*"
)

_SUBSTITUTION = re.compile(
    r"(?<!\w)(" + _GENERIQUE + r"|" + r"|".join(m for _, m in _MOLECULES) + r")(?!\w)"
)
_MOLECULES_COMPILES = tuple(
    (dci, re.compile(rf"(?<!\w)({motif})(?!\w)")) for dci, motif in _MOLECULES
)


def _presence(texte_normalise: str):
    """``("present", empan)`` / ``("nie", empan)`` / ``(None, None)``.

    Négation restreinte aux médicaments (« abstinent sous méthadone » -> present).
    """
    niee = None
    for m in _SUBSTITUTION.finditer(texte_normalise):
        if est_nie_explicite(texte_normalise, m.start(), m.end()):
            niee = niee or m
            continue
        return "present", m.group(0)
    if niee is not None:
        return "nie", niee.group(0)
    return None, None


@enregistrer("traitement_substitution")
class ExtracteurTraitementSubstitution:
    champ = CHAMPS_PAR_CLE["traitement_substitution"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        decision, empan = _presence(texte_normalise)
        if decision == "present":
            return ResultatExtraction(Etat.VRAI, 0.9, empan)
        if decision == "nie":
            return ResultatExtraction(Etat.FAUX, 0.9, empan)
        return ResultatExtraction.absent()


@enregistrer("traitement_substitution_type")
class ExtracteurTraitementSubstitutionType:
    champ = CHAMPS_PAR_CLE["traitement_substitution_type"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        # Le type n'a de sens que si un TSO est avéré.
        if _presence(texte_normalise)[0] != "present":
            return ResultatExtraction.absent()
        for dci, motif in _MOLECULES_COMPILES:
            m = motif.search(texte_normalise)
            if m and not est_nie_explicite(texte_normalise, m.start(), m.end()):
                return ResultatExtraction(dci, 0.9, m.group(0))
        # Mention générique (« sous TSO ») sans molécule précisée.
        return ResultatExtraction.absent()
