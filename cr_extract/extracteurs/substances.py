"""Extracteurs des champs « substances ».

Couvre : alcool (#6), tabac (#7), cannabis/THC/CBD (#8), cocaïne (#9),
cocaïne – voie (#10), héroïne (#11), héroïne – quantité (#12), kétamine (#13).

Deux familles de comportement selon le catalogue :

- **booléen 3 états** (alcool, tabac, kétamine) : ``True`` / ``False`` / ``NA`` ;
- **booléen 2 états** (cocaïne, héroïne) : ``True`` / ``False`` — jamais ``NA``,
  l'absence de mention valant négation (cf. vérité terrain) ;
- **catégoriel** (cannabis, cocaïne-voie) : une sous-catégorie ou ``NA``.
"""

from __future__ import annotations

import re

from cr_extract.modele import (
    CHAMPS_PAR_CLE,
    Etat,
    ResultatExtraction,
)
from cr_extract.negation import evaluer_terme, trouver_occurrences
from cr_extract.extracteurs import enregistrer

# --------------------------------------------------------------------------- #
# Motifs de termes (sur texte normalisé : minuscules, sans accents)
# --------------------------------------------------------------------------- #
_ALCOOL = re.compile(
    r"(?<!\w)(alcool\w*|oh|ethyliqu\w*|oenoliqu\w*|ivre|enivre\w*|biture|\bbu\b|"
    r"buvait|alcoolisation\w*)(?!\w)"
)
_TABAC = re.compile(r"(?<!\w)(tabac\w*|tabagis\w*|fume\w*|fumeu\w*|cigarette\w*|clope\w*|cig)(?!\w)")
_CANNABIS = re.compile(r"(?<!\w)(cannabis|joint\w*|beuh|herbe|shit|weed|ganja)(?!\w)")
_THC = re.compile(r"(?<!\w)thc(?!\w)")
_CBD = re.compile(r"(?<!\w)cbd(?!\w)")
_COCAINE = re.compile(r"(?<!\w)(cocaine|coke|coca|crack)(?!\w)")
_HEROINE = re.compile(r"(?<!\w)(heroine|hero)(?!\w)")
_KETAMINE = re.compile(r"(?<!\w)(ketamine|keta)(?!\w)")

# Voie d'administration de la cocaïne.
_VOIE_NASALE = re.compile(r"(?<!\w)(nasal\w*|sniff\w*|prise\w* nasale\w*)(?!\w)")
_VOIE_IV = re.compile(r"(?<!\w)(intraveineu\w*|\biv\b|inject\w*|injectabl\w*)(?!\w)")

# Quantité d'héroïne : « 0.5 g/j », « ~0.3g », « env 1g/j », « 1.2 g/jour ».
_QUANTITE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*g(?:r|ramme)?s?(?!\w)"
)


def _resultat_3_etats(decision, confiance_present=1.0, confiance_nie=1.0) -> ResultatExtraction:
    """Convertit une décision 3 états en résultat True/False/NA."""
    if decision.valeur == "present":
        return ResultatExtraction(Etat.VRAI, confiance_present, decision.preuve)
    if decision.valeur == "nie":
        return ResultatExtraction(Etat.FAUX, confiance_nie, decision.preuve)
    return ResultatExtraction.absent()


def _resultat_2_etats(decision) -> ResultatExtraction:
    """Convertit une décision en résultat True/False (jamais NA)."""
    if decision.valeur == "present":
        return ResultatExtraction(Etat.VRAI, 1.0, decision.preuve)
    return ResultatExtraction(Etat.FAUX, 1.0, decision.preuve)


# --------------------------------------------------------------------------- #
# Alcool (#6) — 3 états, avec rattrapage des négations globales de consommation
# --------------------------------------------------------------------------- #
# « aucune conso », « pas de consommation d'aucune sorte »… nient l'ensemble des
# consommations : alcool et tabac sont alors comptés comme False même non cités.
_NEG_GLOBALE = re.compile(
    r"(?<!\w)(aucune?\s+conso\w*|aucune?\s+addiction|"
    r"pas\s+de\s+conso\w*(?:\s+d'aucune\s+sorte)?|"
    r"ne\s+consomme\s+pas|aucun\s+toxiqu\w*)"
)


@enregistrer("alcool")
class ExtracteurAlcool:
    champ = CHAMPS_PAR_CLE["alcool"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        decision = evaluer_terme(texte_normalise, _ALCOOL)
        if decision.valeur is None and _NEG_GLOBALE.search(texte_normalise):
            return ResultatExtraction(Etat.FAUX, 0.8, "negation globale de consommation")
        return _resultat_3_etats(decision)


@enregistrer("tabac")
class ExtracteurTabac:
    champ = CHAMPS_PAR_CLE["tabac"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        decision = evaluer_terme(texte_normalise, _TABAC)
        if decision.valeur is None and _NEG_GLOBALE.search(texte_normalise):
            return ResultatExtraction(Etat.FAUX, 0.8, "negation globale de consommation")
        return _resultat_3_etats(decision)


# --------------------------------------------------------------------------- #
# Cannabis / THC / CBD (#8) — catégoriel, sous-catégorie selon le terme
# --------------------------------------------------------------------------- #
@enregistrer("cannabis")
class ExtracteurCannabis:
    champ = CHAMPS_PAR_CLE["cannabis"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        # Priorité CBD > THC > cannabis générique : un terme spécifique présent
        # et affirmé détermine la sous-catégorie.
        for motif, valeur in ((_CBD, "CBD"), (_THC, "THC"), (_CANNABIS, "Cannabis")):
            decision = evaluer_terme(texte_normalise, motif)
            if decision.valeur == "present":
                return ResultatExtraction(valeur, 1.0, decision.preuve)
        # Mention uniquement niée (« pas de cannabis ») ou absente -> NA.
        return ResultatExtraction.absent()


# --------------------------------------------------------------------------- #
# Cocaïne (#9) — 2 états — et voie d'administration (#10) — catégoriel
# --------------------------------------------------------------------------- #
@enregistrer("cocaine")
class ExtracteurCocaine:
    champ = CHAMPS_PAR_CLE["cocaine"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        return _resultat_2_etats(evaluer_terme(texte_normalise, _COCAINE))


@enregistrer("cocaine_voie")
class ExtracteurCocaineVoie:
    champ = CHAMPS_PAR_CLE["cocaine_voie"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        # La voie n'a de sens que si la cocaïne est consommée.
        if evaluer_terme(texte_normalise, _COCAINE).valeur != "present":
            return ResultatExtraction.absent()
        return _voie_administration(texte_normalise, _COCAINE)


# --------------------------------------------------------------------------- #
# Héroïne (#11) — 2 états — et quantité (#12) — numérique
# --------------------------------------------------------------------------- #
@enregistrer("heroine")
class ExtracteurHeroine:
    champ = CHAMPS_PAR_CLE["heroine"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        return _resultat_2_etats(evaluer_terme(texte_normalise, _HEROINE))


@enregistrer("heroine_quantite")
class ExtracteurHeroineQuantite:
    champ = CHAMPS_PAR_CLE["heroine_quantite"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        if evaluer_terme(texte_normalise, _HEROINE).valeur != "present":
            return ResultatExtraction.absent()
        # On cherche une quantité en grammes à proximité d'une mention d'héroïne.
        for occ in trouver_occurrences(texte_normalise, _HEROINE):
            fenetre = texte_normalise[occ.debut:occ.fin + 70]
            m = _QUANTITE.search(fenetre)
            if m:
                valeur = float(m.group(1).replace(",", "."))
                return ResultatExtraction(f"{valeur:.1f}", 0.7, m.group(0).strip())
        return ResultatExtraction.absent()


# --------------------------------------------------------------------------- #
# Kétamine (#13) — 3 états (False = usage révolu)
# --------------------------------------------------------------------------- #
@enregistrer("ketamine")
class ExtracteurKetamine:
    champ = CHAMPS_PAR_CLE["ketamine"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        # « kétamine rapportée par le passé, non actuelle » -> False (révolu) ;
        # mention présente et affirmée -> True ; absente -> NA.
        decision = evaluer_terme(texte_normalise, _KETAMINE)
        # « statut actuel incertain » : usage passé non confirmé -> NA plutôt que
        # False, conformément à la vérité terrain.
        if decision.valeur == "nie" and "incertain" in texte_normalise:
            return ResultatExtraction.absent()
        return _resultat_3_etats(decision)


# --------------------------------------------------------------------------- #
# Voie d'administration (factorisé cocaïne / héroïne)
# --------------------------------------------------------------------------- #
def _voie_administration(texte_normalise: str, motif_substance: re.Pattern) -> ResultatExtraction:
    """Détermine la voie (nasale / intraveineuse) la plus proche de la substance."""
    nasale = _VOIE_NASALE.search(texte_normalise)
    iv = _VOIE_IV.search(texte_normalise)
    if nasale and not iv:
        return ResultatExtraction("nasale", 1.0, nasale.group(0))
    if iv and not nasale:
        return ResultatExtraction("intraveineuse", 1.0, iv.group(0))
    if not nasale and not iv:
        return ResultatExtraction.absent()
    # Les deux voies sont citées : on retient celle la plus proche d'une
    # occurrence de la substance.
    ancre = next(iter(trouver_occurrences(texte_normalise, motif_substance)), None)
    if ancre is None:
        return ResultatExtraction.absent()
    d_nasale = abs(nasale.start() - ancre.debut)
    d_iv = abs(iv.start() - ancre.debut)
    if d_nasale <= d_iv:
        return ResultatExtraction("nasale", 0.7, nasale.group(0))
    return ResultatExtraction("intraveineuse", 0.7, iv.group(0))
