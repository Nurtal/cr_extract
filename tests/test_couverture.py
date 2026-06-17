"""Test de couverture des tags : ce qui est (ou non) couvert par un extracteur."""

from pathlib import Path

from cr_extract.chargement import CompteRendu
from cr_extract.modele import CHAMPS
from cr_extract.extracteurs import extracteurs_disponibles
from cr_extract.corpus import charger_corpus
from cr_extract.couverture import couverture_tags, tags_non_couverts, rapport_couverture

CORPUS = Path(__file__).resolve().parent.parent / "corpus"


def test_tous_les_champs_du_catalogue_ont_un_extracteur():
    # Garde-fou : aucun champ déclaré ne doit rester sans extracteur.
    extracteurs = extracteurs_disponibles()
    manquants = [c.cle for c in CHAMPS if c.cle not in extracteurs]
    assert not manquants, f"champs du catalogue sans extracteur : {manquants}"


def test_tags_non_couverts_sont_hors_catalogue():
    # Tout tag non couvert dans le corpus est nécessairement un tag expérimental
    # (hors du catalogue) : on ne « perd » jamais un champ déclaré.
    couverture = couverture_tags(charger_corpus(CORPUS))
    for tag in tags_non_couverts(couverture):
        assert not couverture[tag].dans_catalogue, (
            f"tag '{tag}' annoté, dans le catalogue, mais sans extracteur"
        )


def test_couverture_detecte_un_tag_experimental():
    # 'tag_fictif' n'a aucun extracteur : il doit ressortir comme non couvert.
    crs = [
        CompteRendu(texte="x", gold={"alcool": "True", "tag_fictif": "True"}, index=0),
    ]
    couverture = couverture_tags(crs)
    assert couverture["alcool"].couvert is True
    assert couverture["tag_fictif"].couvert is False
    assert couverture["tag_fictif"].occurrences == 1
    assert "tag_fictif" in tags_non_couverts(couverture)
    assert "alcool" not in tags_non_couverts(couverture)


def test_occurrences_et_distribution_des_valeurs():
    crs = [
        CompteRendu(texte="a", gold={"alcool": "True"}, index=0),
        CompteRendu(texte="b", gold={"alcool": "False"}, index=1),
        CompteRendu(texte="c", gold={"alcool": "True"}, index=2),
    ]
    cov = couverture_tags(crs)["alcool"]
    assert cov.occurrences == 3
    assert cov.valeurs["True"] == 2 and cov.valeurs["False"] == 1


def test_rapport_couverture_liste_les_tags_experimentaux():
    rapport = rapport_couverture(couverture_tags(charger_corpus(CORPUS)))
    assert "Couverture des tags" in rapport
    # Les tags expérimentaux du corpus synthétique apparaissent comme non couverts.
    for tag in ("mdma", "grossesse", "lsd"):
        assert tag in rapport
