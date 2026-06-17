"""Brique transverse : détection de négation et logique « 3 états ».

Le cœur du sujet est de distinguer :

- ``True``  : le terme est mentionné et affirmé (« tabac actif ») ;
- ``False`` : le terme est mentionné mais nié (« pas de tabac », « non fumeur ») ;
- ``NA``    : le terme n'est pas abordé dans le compte rendu.

La détection travaille sur le **texte normalisé** (minuscules, sans accents),
produit par :mod:`cr_extract.normalisation`. Les empans renvoyés pour la preuve
sont découpés sur ce même texte (suffisant pour l'audit).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence

# --------------------------------------------------------------------------- #
# Lexique de négation
# --------------------------------------------------------------------------- #
# Marqueurs qui, placés *avant* le terme (dans la même proposition), le nient.
# Ex. « pas d'alcool », « aucun toxique », « sans tabac », « plus de cannabis ».
_NEG_AVANT = (
    "pas",
    "sans",
    "aucun",
    "aucune",
    "ni",
    "nie",
    "nient",
    "denie",
    "denient",
    "absence",
    "non",
    "jamais",
    "plus de",
    "plus d",
    "ancien",
    "ancienne",
    "ex",            # « ex-fumeur », « ex-buveur » : usage révolu
)

# Marqueurs « d'abstinence / d'usage révolu » : peuvent apparaître avant OU après
# le terme dans une fenêtre courte (« alcoolodépendance ancienne, abstinente »,
# « héroïne… abstinent depuis substitution », « usage ancien de kétamine »).
_NEG_AUTOUR = (
    "abstinent",
    "abstinente",
    "abstinence",
    "sevre",
    "sevree",
    "arrete",
    "arretee",
    "passe",          # « par le passé », « rapportée par le passé »
    "non actif",
    "non actuel",
    "non actuelle",
    "revolu",
)
# Note : « ancien·ne » ne figure pas ici. Placé *avant* le terme (« ancien
# fumeur ») il nie (cf. _NEG_AVANT) ; placé *après* (« alcoolodépendance
# ancienne ») il qualifie l'ancienneté d'un usage toujours actif et ne doit donc
# pas nier.

# Frontières de proposition : on ne rattache pas une négation par-delà ces
# signes (la parenthèse fermante clôt une incise, ex. « (quantité non chiffrée),
# cocaïne… » ne doit pas nier la cocaïne).
_FRONTIERES = ".;:!?\n)"

# Fenêtres (en caractères) de recherche autour d'un terme.
FENETRE_AVANT = 45
FENETRE_APRES = 28


def _mot_present(fragment: str, mots: Sequence[str]) -> bool:
    """Vrai si l'un de ``mots`` apparaît comme mot entier dans ``fragment``."""
    for mot in mots:
        if re.search(rf"(?<!\w){re.escape(mot)}(?!\w)", fragment):
            return True
    return False


def _fenetre_avant(texte: str, debut: int) -> str:
    """Fragment précédant le terme, tronqué à la dernière frontière de proposition."""
    fragment = texte[max(0, debut - FENETRE_AVANT):debut]
    coupe = max(fragment.rfind(c) for c in _FRONTIERES)
    return fragment[coupe + 1:] if coupe != -1 else fragment


def _fenetre_apres(texte: str, fin: int) -> str:
    """Fragment suivant le terme, tronqué à la première frontière de proposition."""
    fragment = texte[fin:fin + FENETRE_APRES]
    for i, c in enumerate(fragment):
        if c in _FRONTIERES:
            return fragment[:i]
    return fragment


def est_nie(texte_normalise: str, debut: int, fin: int) -> bool:
    """Détermine si le terme situé sur ``[debut, fin[`` est nié dans son contexte.

    Combine trois patrons :

    1. marqueur de négation avant le terme (« pas de », « sans », « aucun »…) ;
    2. tournure « ne … pas/plus/jamais » à cheval sur le terme ;
    3. marqueur d'abstinence / usage révolu avant **ou** après (fenêtre courte).
    """
    avant = _fenetre_avant(texte_normalise, debut)
    apres = _fenetre_apres(texte_normalise, fin)

    # 1. Négation explicite avant le terme.
    if _mot_present(avant, _NEG_AVANT):
        return True

    # 2. « ne … pas » : « ne »/« n' » avant, « pas/plus/jamais » juste après.
    if re.search(r"(?<!\w)n[e']", avant) and _mot_present(apres, ("pas", "plus", "jamais")):
        return True

    # 2 bis. Réponse négative postposée : « tabac non », « alcool : non ».
    apres_nu = apres.lstrip(" :.-")
    if apres_nu == "non" or apres_nu.startswith("non ") or apres_nu.startswith("non."):
        return True

    # 3. Abstinence / usage révolu (bidirectionnel, fenêtre courte).
    if _mot_present(avant, _NEG_AUTOUR) or _mot_present(apres, _NEG_AUTOUR):
        return True

    return False


# Négation *explicite* (ou arrêt de traitement) : variante stricte pour les
# médicaments, où « abstinence »/« ancien » décrivent le patient et non l'arrêt
# du produit (« abstinence sous acamprosate » ne nie pas l'acamprosate).
_NEG_EXPLICITE = (
    "pas", "sans", "aucun", "aucune", "non", "ni", "nie", "jamais", "absence",
    "arret", "arrete", "arretee", "interrompu", "interrompue", "stoppe", "stoppee",
)


def est_nie_explicite(texte_normalise: str, debut: int, fin: int) -> bool:
    """Négation restreinte aux marqueurs explicites / d'arrêt de traitement.

    Destinée aux médicaments (addictolytiques, substitution) : ne tient pas
    compte de l'abstinence ni de l'ancienneté, qui qualifient le statut du
    patient et non l'arrêt du traitement.
    """
    avant = _fenetre_avant(texte_normalise, debut)
    if _mot_present(avant, _NEG_EXPLICITE):
        return True
    apres = _fenetre_apres(texte_normalise, fin)
    return bool(
        re.search(r"(?<!\w)n[e']", avant)
        and _mot_present(apres, ("pas", "plus", "jamais"))
    )


# --------------------------------------------------------------------------- #
# Recherche d'occurrences de termes
# --------------------------------------------------------------------------- #
@dataclass
class Occurrence:
    """Une occurrence d'un terme dans le texte normalisé."""

    debut: int
    fin: int
    texte: str
    nie: bool


def trouver_occurrences(texte_normalise: str, motif: re.Pattern) -> list[Occurrence]:
    """Renvoie toutes les occurrences de ``motif`` avec leur statut de négation."""
    occ = []
    for m in motif.finditer(texte_normalise):
        occ.append(
            Occurrence(
                debut=m.start(),
                fin=m.end(),
                texte=m.group(0),
                nie=est_nie(texte_normalise, m.start(), m.end()),
            )
        )
    return occ


# --------------------------------------------------------------------------- #
# Décision « 3 états » générique
# --------------------------------------------------------------------------- #
@dataclass
class Decision3Etats:
    """Résultat d'une évaluation 3 états sur un terme.

    - ``valeur`` : ``"present"`` (affirmé), ``"nie"`` (nié) ou ``None`` (absent) ;
    - ``preuve`` : empan ayant motivé la décision (ou ``None``).
    """

    valeur: Optional[str]
    preuve: Optional[str] = None


def evaluer_terme(texte_normalise: str, motif: re.Pattern) -> Decision3Etats:
    """Évalue un terme : présent affirmé l'emporte sur présent nié, qui l'emporte
    sur l'absence.

    Une affirmation (au moins une occurrence non niée) prime, car en contexte
    clinique une mention positive du produit traduit un usage avéré même si une
    autre occurrence est niée ailleurs.
    """
    occurrences = trouver_occurrences(texte_normalise, motif)
    if not occurrences:
        return Decision3Etats(valeur=None)

    affirmees = [o for o in occurrences if not o.nie]
    if affirmees:
        return Decision3Etats(valeur="present", preuve=_empan(texte_normalise, affirmees[0]))

    return Decision3Etats(valeur="nie", preuve=_empan(texte_normalise, occurrences[0]))


def _empan(texte: str, occ: Occurrence, marge: int = 18) -> str:
    """Empan de texte autour d'une occurrence, pour la preuve."""
    debut = max(0, occ.debut - marge)
    fin = min(len(texte), occ.fin + marge)
    return texte[debut:fin].strip()
