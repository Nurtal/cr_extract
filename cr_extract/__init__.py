"""CR Extract — extraction d'informations structurées depuis des comptes rendus
médicaux non structurés, par combinaisons de regex.

Toutes les données utilisées dans ce projet sont fictives.
"""

from cr_extract.modele import Champ, ResultatExtraction, Etat
from cr_extract.chargement import CompteRendu, charger_csv
from cr_extract.pipeline import extraire_tout

__all__ = [
    "Champ",
    "ResultatExtraction",
    "Etat",
    "CompteRendu",
    "charger_csv",
    "extraire_tout",
]
