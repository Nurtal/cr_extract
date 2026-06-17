"""Tests de l'API DataFrame (:func:`cr_extract.detecter`).

``polars`` est requis ; les cas pandas sont ignorés si pandas est absent.
"""

import pytest

pl = pytest.importorskip("polars")

from cr_extract import detecter

_DONNEES = {
    "TEXTE": [
        "Patient marié, en activité. Tabac actif. Pas d'alcool. Cocaïne nasale.",
        "Sans domicile fixe. Héroïne IV environ 0.5 g/jour. Pas de cannabis.",
        "Consultation de suivi diabète.",
    ]
}


def test_detecter_ajoute_une_colonne_par_item():
    df = pl.DataFrame(_DONNEES)
    res = detecter(df, items=["alcool", "tabac", "sdf"])
    assert res.columns == ["TEXTE", "alcool", "tabac", "sdf"]
    assert res.height == 3


def test_detecter_ne_modifie_pas_l_entree():
    df = pl.DataFrame(_DONNEES)
    detecter(df, items=["alcool"])
    assert df.columns == ["TEXTE"]


def test_valeurs_booleennes_et_na_null():
    res = detecter(pl.DataFrame(_DONNEES), items=["alcool", "tabac", "sdf", "heroine"])
    # Ligne 0 : tabac affirmé, alcool nié ; ligne 2 : rien -> NA (null).
    assert res["tabac"].to_list() == [True, None, None]
    assert res["alcool"].to_list() == [False, None, None]
    assert res["sdf"].to_list() == [False, True, False]
    assert res["heroine"].to_list() == [False, True, False]
    assert res["tabac"].dtype == pl.Boolean


def test_champ_numerique_en_flottant():
    res = detecter(pl.DataFrame(_DONNEES), items=["heroine_quantite"])
    assert res["heroine_quantite"].to_list() == [None, 0.5, None]
    assert res["heroine_quantite"].dtype == pl.Float64


def test_champ_categoriel_libelle_ou_null():
    res = detecter(pl.DataFrame(_DONNEES), items=["situation_conjugale"])
    assert res["situation_conjugale"].to_list() == ["en couple", None, None]


def test_prefixe_des_colonnes():
    res = detecter(pl.DataFrame(_DONNEES), items=["alcool"], prefixe="item_")
    assert "item_alcool" in res.columns


def test_colonne_texte_personnalisee():
    df = pl.DataFrame({"compte_rendu": _DONNEES["TEXTE"]})
    res = detecter(df, items=["sdf"], colonne_texte="compte_rendu")
    assert res["sdf"].to_list() == [False, True, False]


def test_item_inconnu_leve_valueerror():
    with pytest.raises(ValueError, match="Items inconnus"):
        detecter(pl.DataFrame(_DONNEES), items=["inexistant"])


def test_colonne_texte_absente_leve_valueerror():
    with pytest.raises(ValueError, match="Colonne texte"):
        detecter(pl.DataFrame({"X": [1]}), items=["alcool"])


def test_type_df_invalide_leve_typeerror():
    with pytest.raises(TypeError):
        detecter([{"TEXTE": "abc"}], items=["alcool"])


def test_entree_pandas():
    pd = pytest.importorskip("pandas")
    res = detecter(pd.DataFrame(_DONNEES), items=["alcool", "sdf"])
    assert isinstance(res, pl.DataFrame)
    assert res["sdf"].to_list() == [False, True, False]
