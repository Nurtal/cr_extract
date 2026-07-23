"""CR Extract — extraction d'informations structurées depuis des comptes rendus
médicaux non structurés, par combinaisons de regex.

Toutes les données utilisées dans ce projet sont fictives.
"""

__version__ = "0.2.1"

from cr_extract.modele import Champ, ResultatExtraction, Etat
from cr_extract.chargement import CompteRendu, charger_csv
from cr_extract.pipeline import extraire_tout
from cr_extract.dataframe import detecter
from cr_extract.corpus import charger_corpus, ecrire_corpus, csv_vers_corpus
from cr_extract.couverture import couverture_tags, rapport_couverture, tags_non_couverts

__all__ = [
    "__version__",
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
    "couverture_tags",
    "rapport_couverture",
    "tags_non_couverts",
]
