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

# Négation propre aux médicaments : on ne retient que les négations *explicites*
# ou l'arrêt du traitement. Les marqueurs d'« abstinence » / « ancien » décrivent
# le statut du patient vis-à-vis du produit, pas l'arrêt du médicament, et ne
# doivent donc pas nier un addictolytique (« abstinence sous acamprosate »).
_NEG_MED = re.compile(
    r"(?<!\w)(pas|sans|aucun|aucune|non|ni|arret|arrete\w*|interrompu\w*|stoppe\w*)(?!\w)"
)


def _nie_medicament(texte: str, debut: int, fin: int) -> bool:
    avant = texte[max(0, debut - 40):debut]
    coupe = max((avant.rfind(c) for c in ".;:!?\n)"), default=-1)
    if coupe != -1:
        avant = avant[coupe + 1:]
    if _NEG_MED.search(avant):
        return True
    apres = texte[fin:fin + 18]
    return bool(
        re.search(r"(?<!\w)n[e']", avant)
        and re.search(r"(?<!\w)(pas|plus|jamais)(?!\w)", apres)
    )


def _presence(texte_normalise: str):
    """``("present", empan)`` / ``("nie", empan)`` / ``(None, None)``."""
    niee = None
    for m in _ADDICTOLYTIQUE.finditer(texte_normalise):
        if _nie_medicament(texte_normalise, m.start(), m.end()):
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
            if m and not _nie_medicament(texte_normalise, m.start(), m.end()):
                return ResultatExtraction(dci, 0.9, m.group(0))
        # Mention générique (« traitement de substitution ») sans molécule.
        return ResultatExtraction.absent()
