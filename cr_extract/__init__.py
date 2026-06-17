"""CR Extract — extraction d'informations structurées depuis des comptes rendus
médicaux non structurés, par combinaisons de regex.

Toutes les données utilisées dans ce projet sont fictives.
"""

from cr_extract.modele import Champ, ResultatExtraction, Etat
from cr_extract.chargement import CompteRendu, charger_csv
from cr_extract.pipeline import extraire_tout
from cr_extract.dataframe import detecter
from cr_extract.corpus import charger_corpus, ecrire_corpus, csv_vers_corpus

__all__ = [
    "Champ",
    "ResultatExtraction",
    "Etat",
    "CompteRendu",
    "charger_csv",
    "extraire_tout",
    "detecter",
    "charger_corpus",
    "ecrire_corpus",
    "csv_vers_corpus",
]
