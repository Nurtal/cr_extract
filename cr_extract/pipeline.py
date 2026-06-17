"""Orchestration : applique tous les extracteurs enregistrés à un texte.

Point d'entrée commun à l'évaluation et à la CLI. Le texte est normalisé une
seule fois (cf. :mod:`cr_extract.normalisation`) puis transmis à chaque
extracteur, qui dispose aussi du texte d'origine pour la preuve.
"""

from __future__ import annotations

from cr_extract.modele import CHAMPS, ResultatExtraction
from cr_extract.normalisation import normaliser
from cr_extract.extracteurs import extracteurs_disponibles


def extraire_tout(texte: str) -> dict[str, ResultatExtraction]:
    """Extrait les 13 champs d'un compte rendu.

    Renvoie un dictionnaire ``{cle_champ: ResultatExtraction}`` couvrant tous les
    champs du catalogue. Les champs sans extracteur enregistré renvoient ``NA``.
    """
    texte_normalise = normaliser(texte)
    extracteurs = extracteurs_disponibles()
    resultats: dict[str, ResultatExtraction] = {}
    for champ in CHAMPS:
        extracteur = extracteurs.get(champ.cle)
        if extracteur is None:
            resultats[champ.cle] = ResultatExtraction.absent()
        else:
            resultats[champ.cle] = extracteur.extraire(texte_normalise, texte)
    return resultats
