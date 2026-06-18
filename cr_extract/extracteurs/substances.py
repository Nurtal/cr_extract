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
from cr_extract.negation import (
    Decision3Etats,
    est_entourage,
    evaluer_terme,
    trouver_occurrences,
    _empan,
)
from cr_extract.extracteurs import enregistrer

# --------------------------------------------------------------------------- #
# Motifs de termes (sur texte normalisé : minuscules, sans accents)
# --------------------------------------------------------------------------- #
_ALCOOL = re.compile(
    r"(?<!\w)(alcool\w*|oh|ethyliqu\w*|oenoliqu\w*|ivre|enivre\w*|biture|\bbu\b|"
    r"buvait|alcoolisation\w*|vin|biere\w*|pastis|whisky|cognac)(?!\w)"
)
# Étiologie : un alcool « descripteur de pathologie » (« cirrhose OH »,
# « pancréatite éthylique ») atteste l'imputabilité, mais ne tranche pas seul la
# consommation *actuelle* face à un arrêt explicite (« OH stoppé »).
_ETIOLOGIE = re.compile(
    r"(cirrhos|pancreatit|hepatopathi|hepatit|cytolys|steatos|encephalopath|"
    r"cardiopathi|myocardiopath|neuropath|gastrit|oesophagit)\w*"
)
_TABAC = re.compile(r"(?<!\w)(tabac\w*|tabagis\w*|fume\w*|fumeu\w*|cigarette\w*|clope\w*|cig)(?!\w)")
_CANNABIS = re.compile(r"(?<!\w)(cannabis|joint\w*|beuh|herbe|shit|weed|ganja)(?!\w)")
_THC = re.compile(r"(?<!\w)thc(?!\w)")
_CBD = re.compile(r"(?<!\w)cbd(?!\w)")
_COCAINE = re.compile(r"(?<!\w)(cocaine|coke|coca|crack)(?!\w)")
_HEROINE = re.compile(r"(?<!\w)(heroine|hero)(?!\w)")
_KETAMINE = re.compile(r"(?<!\w)(ketamine|keta)(?!\w)")
_MDMA = re.compile(r"(?<!\w)(mdma|ecstasy|extasy|exta|molly)(?!\w)")
_LSD = re.compile(r"(?<!\w)(lsd|buvard\w*|diethylamide)(?!\w)")
_AMPHETAMINES = re.compile(
    r"(?<!\w)(amphet\w*|speed|methamphetamine\w*|metamphetamine\w*|crystal\s*meth)(?!\w)"
)

# Voie d'administration de la cocaïne.
_VOIE_NASALE = re.compile(r"(?<!\w)(nasal\w*|sniff\w*|prise\w* nasale\w*)(?!\w)")
_VOIE_IV = re.compile(r"(?<!\w)(intraveineu\w*|\biv\b|inject\w*|injectabl\w*)(?!\w)")

# Quantité d'héroïne : « 0.5 g/j », « ~0.3g », « env 1g/j », « 1.2 g/jour ».
_QUANTITE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*g(?:r|ramme)?s?(?!\w)"
)


def _est_etiologie(texte_normalise: str, debut: int) -> bool:
    """Vrai si la mention sert de descripteur étiologique d'une pathologie
    (« cirrhose OH », « pancréatite éthylique ») juste avant le terme."""
    return bool(_ETIOLOGIE.search(texte_normalise[max(0, debut - 30):debut]))


def _decision_consommation(texte_normalise, motif, *, etiologie: bool = False) -> Decision3Etats:
    """Décision 3 états « consommation » sous forme d'arbre :

    1. on écarte les mentions rattachées à l'entourage (« père alcoolique ») ;
    2. une consommation actuelle affirmée (hors étiologie) -> ``present`` ;
    3. sinon un arrêt / une négation explicite -> ``nie`` (prime sur l'étiologie
       seule : « cirrhose OH … OH stoppé » = arrêt) ;
    4. sinon une étiologie affirmée seule (« cirrhose OH ») -> ``present`` ;
    5. sinon -> absence.
    """
    occ = trouver_occurrences(texte_normalise, motif)
    pertinentes = [o for o in occ if not est_entourage(texte_normalise, o.debut)]
    if not pertinentes:
        return Decision3Etats(valeur=None)

    affirmees = [o for o in pertinentes if not o.nie]
    niees = [o for o in pertinentes if o.nie]

    if etiologie:
        reelles = [o for o in affirmees if not _est_etiologie(texte_normalise, o.debut)]
        if reelles:
            return Decision3Etats("present", _empan(texte_normalise, reelles[0]))
        if niees:
            return Decision3Etats("nie", _empan(texte_normalise, niees[0]))
        if affirmees:  # étiologie affirmée seule, sans arrêt -> usage attesté
            return Decision3Etats("present", _empan(texte_normalise, affirmees[0]))
        return Decision3Etats(valeur=None)

    if affirmees:
        return Decision3Etats("present", _empan(texte_normalise, affirmees[0]))
    if niees:
        return Decision3Etats("nie", _empan(texte_normalise, niees[0]))
    return Decision3Etats(valeur=None)


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
        decision = _decision_consommation(texte_normalise, _ALCOOL, etiologie=True)
        if decision.valeur is None and _NEG_GLOBALE.search(texte_normalise):
            return ResultatExtraction(Etat.FAUX, 0.8, "negation globale de consommation")
        return _resultat_3_etats(decision)


@enregistrer("tabac")
class ExtracteurTabac:
    champ = CHAMPS_PAR_CLE["tabac"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        decision = _decision_consommation(texte_normalise, _TABAC)
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
# MDMA (#), LSD (#), amphétamines (#) — 3 états (présence festive/récréative)
# --------------------------------------------------------------------------- #
@enregistrer("mdma")
class ExtracteurMdma:
    champ = CHAMPS_PAR_CLE["mdma"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        return _resultat_3_etats(evaluer_terme(texte_normalise, _MDMA))


@enregistrer("lsd")
class ExtracteurLsd:
    champ = CHAMPS_PAR_CLE["lsd"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        return _resultat_3_etats(evaluer_terme(texte_normalise, _LSD))


@enregistrer("amphetamines")
class ExtracteurAmphetamines:
    champ = CHAMPS_PAR_CLE["amphetamines"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        return _resultat_3_etats(evaluer_terme(texte_normalise, _AMPHETAMINES))


# --------------------------------------------------------------------------- #
# Voie d'administration (factorisé cocaïne / héroïne)
# --------------------------------------------------------------------------- #
def _voie_administration(texte_normalise: str, motif_substance: re.Pattern) -> ResultatExtraction:
    """Détermine la voie (nasale / intraveineuse) la plus proche de la substance.

    Les voies *niées* (« pas par voie nasale ni injectée » — typiquement un crack
    fumé) sont écartées : aucune voie affirmée -> ``NA``.
    """
    nasales = [o for o in trouver_occurrences(texte_normalise, _VOIE_NASALE) if not o.nie]
    ivs = [o for o in trouver_occurrences(texte_normalise, _VOIE_IV) if not o.nie]
    if nasales and not ivs:
        return ResultatExtraction("nasale", 1.0, nasales[0].texte)
    if ivs and not nasales:
        return ResultatExtraction("intraveineuse", 1.0, ivs[0].texte)
    if not nasales and not ivs:
        return ResultatExtraction.absent()
    # Les deux voies sont affirmées : on retient celle la plus proche d'une
    # occurrence de la substance.
    ancre = next(iter(trouver_occurrences(texte_normalise, motif_substance)), None)
    if ancre is None:
        return ResultatExtraction.absent()
    d_nasale = min(abs(o.debut - ancre.debut) for o in nasales)
    d_iv = min(abs(o.debut - ancre.debut) for o in ivs)
    if d_nasale <= d_iv:
        return ResultatExtraction("nasale", 0.7, nasales[0].texte)
    return ResultatExtraction("intraveineuse", 0.7, ivs[0].texte)
