"""Tests du corpus JSON (écriture, chargement, équivalence avec le CSV)."""

import json
from pathlib import Path

from cr_extract.chargement import CompteRendu
from cr_extract.corpus import ecrire_corpus, charger_corpus, csv_vers_corpus
from cr_extract.evaluation import evaluer_corpus, evaluer_fichier

CSV_REFERENCE = Path(__file__).resolve().parent.parent / "comptes_rendus_medicaux.csv"


def test_ecrire_puis_charger_round_trip(tmp_path):
    crs = [
        CompteRendu(texte="Patient marié, tabac actif.",
                    gold={"situation_conjugale": "en couple", "tabac": "True"}, index=0),
        CompteRendu(texte="SDF, pas d'alcool.",
                    gold={"sdf": "True", "alcool": "False"}, index=1),
    ]
    ecrire_corpus(crs, tmp_path)
    recharges = charger_corpus(tmp_path)
    assert [c.texte for c in recharges] == [c.texte for c in crs]
    assert [c.gold for c in recharges] == [c.gold for c in crs]


def test_fichier_json_bien_forme(tmp_path):
    ecrire_corpus(
        [CompteRendu(texte="abc", gold={"alcool": "True"}, index=0)], tmp_path
    )
    donnees = json.loads((tmp_path / "cr_000.json").read_text(encoding="utf-8"))
    assert donnees["id"] == "cr_000"
    assert donnees["texte"] == "abc"
    assert donnees["tags"] == {"alcool": "True"}


def test_tag_supplementaire_conserve(tmp_path):
    # Un tag inédit (futur extracteur) doit être conservé au round-trip.
    crs = [CompteRendu(texte="x", gold={"alcool": "True", "benzodiazepines": "True"}, index=0)]
    ecrire_corpus(crs, tmp_path)
    assert charger_corpus(tmp_path)[0].gold["benzodiazepines"] == "True"


def test_annotation_partielle_ignoree_a_l_evaluation(tmp_path):
    # Seul 'alcool' est annoté : les autres champs ne comptent pas.
    ecrire_corpus(
        [CompteRendu(texte="Pas d'alcool.", gold={"alcool": "False"}, index=0)], tmp_path
    )
    scores = evaluer_corpus(tmp_path)
    assert scores["alcool"].total == 1
    assert scores["tabac"].total == 0


def test_corpus_equivaut_au_csv(tmp_path):
    csv_vers_corpus(CSV_REFERENCE, tmp_path)
    par_csv = evaluer_fichier(CSV_REFERENCE)
    par_corpus = evaluer_corpus(tmp_path)
    for cle in par_csv:
        assert par_csv[cle].corrects == par_corpus[cle].corrects
        assert par_csv[cle].total == par_corpus[cle].total
