"""Modèles de données partagés : catalogue des champs cibles, résultat
d'extraction et interface commune des extracteurs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol


# --------------------------------------------------------------------------- #
# Valeurs canoniques
# --------------------------------------------------------------------------- #
# Les champs booléens « 3 états » utilisent ces chaînes, identiques à celles du
# CSV de référence, pour permettre une comparaison directe avec la vérité terrain.
class Etat:
    VRAI = "True"   # item présent / affirmé
    FAUX = "False"  # item nié explicitement
    NA = "NA"       # item non mentionné dans le compte rendu


# --------------------------------------------------------------------------- #
# Catalogue des champs cibles
# --------------------------------------------------------------------------- #
TYPE_BOOLEEN = "booleen"        # True / False / NA
TYPE_CATEGORIEL = "categoriel"  # une valeur parmi une liste fermée (+ NA)
TYPE_NUMERIQUE = "numerique"    # nombre flottant ou NA


@dataclass(frozen=True)
class Champ:
    """Décrit un champ cible à extraire.

    - ``cle`` : identifiant interne stable (snake_case), utilisé dans le code.
    - ``colonne`` : intitulé exact de la colonne dans le CSV de référence.
    - ``type_`` : nature du champ (booléen / catégoriel / numérique).
    - ``valeurs`` : valeurs autorisées (hors NA) pour les champs catégoriels.
    """

    cle: str
    colonne: str
    type_: str
    valeurs: tuple[str, ...] = ()


# Les 13 champs, dans l'ordre des colonnes du CSV.
CHAMPS: tuple[Champ, ...] = (
    Champ("situation_conjugale", "Célibataire / en couple", TYPE_CATEGORIEL,
          ("en couple", "célibataire")),
    Champ("situation_professionnelle", "Situation professionnelle", TYPE_CATEGORIEL,
          ("actif", "inactif")),
    Champ("sdf", "SDF / absence de logement", TYPE_BOOLEEN),
    Champ("protection_juridique", "Curatelle / Tutelle", TYPE_CATEGORIEL,
          ("curatelle", "tutelle")),
    Champ("sevrages_compliques", "Antécédents de sevrages compliqués", TYPE_BOOLEEN),
    Champ("alcool", "Consommation actuelle d'alcool", TYPE_BOOLEEN),
    Champ("tabac", "Consommation actuelle de tabac", TYPE_BOOLEEN),
    Champ("cannabis", "Cannabis / THC / CBD", TYPE_CATEGORIEL,
          ("Cannabis", "THC", "CBD")),
    Champ("cocaine", "Cocaïne", TYPE_BOOLEEN),
    Champ("cocaine_voie", "Cocaïne - voie d'administration", TYPE_CATEGORIEL,
          ("nasale", "intraveineuse")),
    Champ("heroine", "Héroïne", TYPE_BOOLEEN),
    Champ("heroine_quantite", "Héroïne - quantité", TYPE_NUMERIQUE),
    Champ("ketamine", "Kétamine", TYPE_BOOLEEN),
    # Champs additionnels (hors CSV de référence d'origine).
    Champ("benzodiazepines", "Benzodiazépines", TYPE_BOOLEEN),
    Champ("benzodiazepine_type", "Benzodiazépine - type", TYPE_CATEGORIEL,
          ("alprazolam", "bromazepam", "clobazam", "clonazepam", "clorazepate",
           "diazepam", "flunitrazepam", "lorazepam", "lormetazepam", "midazolam",
           "nitrazepam", "oxazepam", "prazepam", "temazepam", "zolpidem",
           "zopiclone")),
    Champ("hypnotiques", "Hypnotiques", TYPE_BOOLEEN),
    Champ("hypnotique_type", "Hypnotique - type", TYPE_CATEGORIEL,
          ("doxylamine", "estazolam", "flunitrazepam", "loprazolam",
           "lormetazepam", "melatonine", "nitrazepam", "temazepam",
           "zolpidem", "zopiclone")),
    Champ("addictolytique", "Addictolytique", TYPE_BOOLEEN),
    Champ("addictolytique_type", "Addictolytique - type", TYPE_CATEGORIEL,
          ("acamprosate", "baclofene", "buprenorphine", "bupropion",
           "disulfirame", "methadone", "nalmefene", "naltrexone", "nicotine",
           "varenicline")),
    Champ("traitement_substitution", "Traitement de substitution", TYPE_BOOLEEN),
    Champ("traitement_substitution_type", "Traitement de substitution - type",
          TYPE_CATEGORIEL, ("buprenorphine", "methadone")),
    Champ("mdma", "MDMA", TYPE_BOOLEEN),
    Champ("lsd", "LSD", TYPE_BOOLEEN),
    Champ("amphetamines", "Amphétamines", TYPE_BOOLEEN),
    Champ("grossesse", "Grossesse", TYPE_BOOLEEN),
    Champ("hepatopathie", "Hépatopathie", TYPE_BOOLEEN),
    Champ("suivi_hepato_gastro", "Suivi hépato-gastro-entérologie", TYPE_BOOLEEN),
    Champ("pancreatite", "Pancréatite", TYPE_BOOLEEN),
    Champ("cardiovasculaire", "Problèmes cardiovasculaires", TYPE_BOOLEEN),
    Champ("bpco", "BPCO", TYPE_BOOLEEN),
    Champ("emphyseme", "Emphysème", TYPE_BOOLEEN),
    Champ("diabete", "Diabète", TYPE_BOOLEEN),
)

# Index par clé interne et par intitulé de colonne, pour les recherches rapides.
CHAMPS_PAR_CLE: dict[str, Champ] = {c.cle: c for c in CHAMPS}
CHAMPS_PAR_COLONNE: dict[str, Champ] = {c.colonne: c for c in CHAMPS}


# --------------------------------------------------------------------------- #
# Résultat d'extraction
# --------------------------------------------------------------------------- #
@dataclass
class ResultatExtraction:
    """Résultat produit par un extracteur pour un champ donné.

    - ``valeur`` : valeur extraite (chaîne canonique du champ, ou ``Etat.NA``).
    - ``confiance`` : score dans [0, 1] (1 = certain). Surtout utile pour les
      champs difficiles ; les champs triviaux peuvent rester à 1.0.
    - ``preuve`` : empan de texte ayant déclenché la décision (traçabilité /
      audit clinique). ``None`` si la valeur est NA par absence de signal.
    """

    valeur: str
    confiance: float = 1.0
    preuve: Optional[str] = None

    @classmethod
    def absent(cls) -> "ResultatExtraction":
        """Raccourci : champ non mentionné dans le compte rendu."""
        return cls(valeur=Etat.NA, confiance=1.0, preuve=None)


# --------------------------------------------------------------------------- #
# Interface commune des extracteurs
# --------------------------------------------------------------------------- #
class Extracteur(Protocol):
    """Contrat que doit respecter tout extracteur de champ.

    Un extracteur reçoit le texte normalisé (et le texte d'origine pour la
    preuve) et renvoie un :class:`ResultatExtraction`.
    """

    champ: Champ

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        ...
