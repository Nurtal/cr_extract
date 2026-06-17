"""Extracteurs des addictolytiques : traitement médicamenteux de l'addiction.

- ``addictolytique`` (booléen 3 états) : présence d'un traitement de l'addiction
  — anti-craving, aversion, substitution aux opiacés (TSO), aide au sevrage
  tabagique. ``True`` si affirmé, ``False`` si nié, ``NA`` si non abordé.
- ``addictolytique_type`` (catégoriel) : molécule (DCI) si elle est nommée,
  sinon ``NA``.

Couvre plusieurs familles :

- alcool : acamprosate, naltrexone, nalméfène, disulfirame, baclofène ;
- opiacés (TSO) : méthadone, buprénorphine ;
- tabac : varénicline, bupropion, substituts nicotiniques.

Attention : la **naloxone** (antidote d'overdose) n'est *pas* un addictolytique
et est volontairement exclue ; seule la *naltrexone* (anti-craving) est retenue.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, Etat, ResultatExtraction
from cr_extract.negation import est_nie_explicite
from cr_extract.extracteurs import enregistrer

# Molécules (DCI canonique -> motif DCI + noms commerciaux / variantes).
_MOLECULES: tuple[tuple[str, str], ...] = (
    ("acamprosate", r"acamprosate|aotal"),
    ("naltrexone", r"naltrexone|revia|nalorex"),
    ("nalmefene", r"nalmefene|selincro"),
    ("disulfirame", r"disulfiram\w*|esperal"),
    ("baclofene", r"baclofene|baclocur"),
    ("methadone", r"methadone|metha"),
    ("buprenorphine", r"buprenorphine|subutex|suboxone|\bbhd\b"),
    ("varenicline", r"varenicline|champix"),
    ("bupropion", r"bupropion|zyban"),
    ("nicotine", r"substituts? nicotiniques?|substitution nicotinique|"
                 r"patchs? nicotiniques?|\btns\b|nicotine"),
)

# Termes génériques (traitement de l'addiction sans molécule précise).
_GENERIQUE = (
    r"addictolytique\w*|traitement de substitution|substitution aux opiaces|"
    r"\btso\b|anti[- ]?craving|traitement anti[- ]?craving|"
    r"traitement de l'addiction|medicament de l'addiction"
)

_ADDICTOLYTIQUE = re.compile(
    r"(?<!\w)(" + _GENERIQUE + r"|" + r"|".join(m for _, m in _MOLECULES) + r")(?!\w)"
)
_MOLECULES_COMPILES = tuple(
    (dci, re.compile(rf"(?<!\w)({motif})(?!\w)")) for dci, motif in _MOLECULES
)

def _presence(texte_normalise: str):
    """``("present", empan)`` / ``("nie", empan)`` / ``(None, None)``.

    Utilise une négation restreinte aux médicaments (cf.
    :func:`negation.est_nie_explicite`) : « abstinence sous acamprosate » reste
    ``present``.
    """
    niee = None
    for m in _ADDICTOLYTIQUE.finditer(texte_normalise):
        if est_nie_explicite(texte_normalise, m.start(), m.end()):
            niee = niee or m
            continue
        return "present", m.group(0)
    if niee is not None:
        return "nie", niee.group(0)
    return None, None


@enregistrer("addictolytique")
class ExtracteurAddictolytique:
    champ = CHAMPS_PAR_CLE["addictolytique"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        decision, empan = _presence(texte_normalise)
        if decision == "present":
            return ResultatExtraction(Etat.VRAI, 0.9, empan)
        if decision == "nie":
            return ResultatExtraction(Etat.FAUX, 0.9, empan)
        return ResultatExtraction.absent()


@enregistrer("addictolytique_type")
class ExtracteurAddictolytiqueType:
    champ = CHAMPS_PAR_CLE["addictolytique_type"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        # Le type n'a de sens que si un addictolytique est avéré.
        if _presence(texte_normalise)[0] != "present":
            return ResultatExtraction.absent()
        # Première molécule nommée et affirmée.
        for dci, motif in _MOLECULES_COMPILES:
            m = motif.search(texte_normalise)
            if m and not est_nie_explicite(texte_normalise, m.start(), m.end()):
                return ResultatExtraction(dci, 0.9, m.group(0))
        # Mention générique (« traitement de substitution ») sans molécule.
        return ResultatExtraction.absent()
