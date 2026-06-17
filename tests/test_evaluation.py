"""Tests du harnais d'évaluation et du pipeline (Phase 5)."""

from pathlib import Path

from cr_extract.modele import CHAMPS
from cr_extract.pipeline import extraire_tout
from cr_extract.evaluation import evaluer_fichier, rapport_markdown

CSV_REFERENCE = Path(__file__).resolve().parent.parent / "comptes_rendus_medicaux.csv"

# Seuils minimaux par champ (cf. ROADMAP : >=90% faciles, >=75% difficiles).
# On vérifie un plancher prudent, sous le score courant, pour détecter les
# régressions sans rendre les tests fragiles aux petites variations.
_PLANCHERS = {
    "situation_conjugale": 0.90,
    "situation_professionnelle": 0.85,
    "sdf": 0.85,
    "protection_juridique": 0.95,
    "sevrages_compliques": 0.85,
    "alcool": 0.88,
    "tabac": 0.92,
    "cannabis": 0.95,
    "cocaine": 0.95,
    "cocaine_voie": 0.95,
    "heroine": 0.95,
    "heroine_quantite": 0.95,
    "ketamine": 0.95,
}


def test_pipeline_couvre_les_13_champs():
    resultats = extraire_tout("Patient marié, en activité. Tabac actif. Pas d'alcool.")
    assert set(resultats) == {c.cle for c in CHAMPS}


def test_accuracy_globale_au_dessus_du_seuil():
    scores = evaluer_fichier(CSV_REFERENCE)
    total = sum(s.total for s in scores.values())
    corrects = sum(s.corrects for s in scores.values())
    assert corrects / total >= 0.95


def test_planchers_par_champ():
    scores = evaluer_fichier(CSV_REFERENCE)
    sous_seuil = {
        cle: round(scores[cle].accuracy, 3)
        for cle, plancher in _PLANCHERS.items()
        if scores[cle].accuracy < plancher
    }
    assert not sous_seuil, f"champs sous le plancher attendu : {sous_seuil}"


def test_rapport_markdown_bien_forme():
    scores = evaluer_fichier(CSV_REFERENCE)
    rapport = rapport_markdown(scores)
    assert "Accuracy globale" in rapport
    for champ in CHAMPS:
        assert champ.cle in rapport
