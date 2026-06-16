"""Tests du socle (Phase 1) : modèle, normalisation, chargement CSV."""

from pathlib import Path

import pytest

from cr_extract.modele import (
    CHAMPS,
    CHAMPS_PAR_CLE,
    CHAMPS_PAR_COLONNE,
    Etat,
    ResultatExtraction,
)
from cr_extract.normalisation import normaliser, retirer_accents
from cr_extract.chargement import charger_csv

CSV_REFERENCE = Path(__file__).resolve().parent.parent / "comptes_rendus_medicaux.csv"


# --- Modèle ---------------------------------------------------------------- #
def test_catalogue_contient_13_champs():
    assert len(CHAMPS) == 13


def test_index_coherents_avec_le_catalogue():
    assert set(CHAMPS_PAR_CLE.values()) == set(CHAMPS)
    assert set(CHAMPS_PAR_COLONNE.values()) == set(CHAMPS)
    assert len(CHAMPS_PAR_CLE) == 13
    assert len(CHAMPS_PAR_COLONNE) == 13


def test_resultat_absent():
    r = ResultatExtraction.absent()
    assert r.valeur == Etat.NA
    assert r.confiance == 1.0
    assert r.preuve is None


# --- Normalisation --------------------------------------------------------- #
def test_retirer_accents():
    assert retirer_accents("célibataire") == "celibataire"
    assert retirer_accents("Cocaïne") == "Cocaine"


def test_normaliser_minuscule_accents_espaces():
    assert normaliser("Pas   d'alcool\n déclaré") == "pas d'alcool declare"


def test_normaliser_apostrophe_typographique():
    assert normaliser("consommation d’alcool") == "consommation d'alcool"


# --- Chargement ------------------------------------------------------------ #
def test_chargement_csv_reference():
    crs = charger_csv(CSV_REFERENCE)
    assert len(crs) == 100

    premier = crs[0]
    assert premier.texte.startswith("COMPTE RENDU D'HOSPITALISATION")
    # Les 13 champs gold doivent être présents.
    assert len(premier.gold) == 13
    assert premier.gold["situation_conjugale"] == "en couple"
    assert premier.gold["alcool"] == Etat.VRAI
    assert premier.gold["cocaine"] == Etat.FAUX


def test_chargement_index_croissants():
    crs = charger_csv(CSV_REFERENCE)
    assert [cr.index for cr in crs] == list(range(100))
