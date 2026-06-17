"""Tests unitaires par extracteur (cas limites issus du CSV de référence).

On passe par le pipeline complet : ``extraire_tout`` renvoie un dictionnaire
``{cle_champ: ResultatExtraction}``. Les cas sont des reformulations fidèles des
formulations rencontrées dans les comptes rendus.
"""

import pytest

from cr_extract.modele import Etat
from cr_extract.pipeline import extraire_tout


def val(texte: str, cle: str) -> str:
    return extraire_tout(texte)[cle].valeur


# --- Situation conjugale (#1) ---------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Patient marié, deux enfants.", "en couple"),
    ("Elle vit en couple avec son conjoint.", "en couple"),
    ("Monsieur célibataire, vit seul.", "célibataire"),
    ("Divorcé donc actuellement célibataire.", "célibataire"),
    ("Veuf, retraité.", "célibataire"),
    ("Prise en charge psychiatrique et sociale conjointe.", "NA"),  # « conjointe » != conjoint
    ("Situation conjugale non renseignée.", "NA"),
])
def test_situation_conjugale(texte, attendu):
    assert val(texte, "situation_conjugale") == attendu


# --- Situation professionnelle (#2) ---------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Cadre, en activité.", "actif"),
    ("Étudiant en deuxième année.", "actif"),
    ("En intérim depuis six mois.", "actif"),
    ("Sans emploi depuis plusieurs années.", "inactif"),
    ("En arrêt de travail prolongé (chauffeur poids lourd).", "inactif"),
    ("Retraité de la fonction publique.", "inactif"),
    ("Bénéficiaire de l'AAH.", "inactif"),
    ("Tabagisme actif, pas d'autre information.", "NA"),  # « actif » qualifie le tabac
    ("Amené par la police, mutique.", "NA"),
])
def test_situation_professionnelle(texte, attendu):
    assert val(texte, "situation_professionnelle") == attendu


# --- SDF / logement (#3) --------------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Patient SDF depuis deux ans, pas de logement stable.", Etat.VRAI),
    ("Sans domicile fixe, vivant à la rue.", Etat.VRAI),
    ("Marié, en activité, retour à domicile.", Etat.FAUX),
    ("Hébergé chez ses parents.", Etat.FAUX),
    ("Hébergement non précisé à l'entrée.", Etat.NA),
    ("Hébergé temporairement chez un ami.", Etat.NA),
])
def test_sdf(texte, attendu):
    assert val(texte, "sdf") == attendu


# --- Protection juridique (#4) --------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Sous curatelle renforcée.", "curatelle"),
    ("Une mesure de tutelle a été prononcée.", "tutelle"),
    ("Pas de mesure de protection juridique.", "NA"),
    ("Sous sauvegarde de justice.", "NA"),  # hors catalogue
])
def test_protection_juridique(texte, attendu):
    assert val(texte, "protection_juridique") == attendu


# --- Sevrages compliqués (#5) ---------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Antécédent de delirium tremens lors d'un sevrage non encadré.", Etat.VRAI),
    ("Plusieurs DT dans le passé d'après le dossier.", Etat.VRAI),
    ("Deux sevrages antérieurs compliqués.", Etat.VRAI),
    ("Sevrage spontané difficile il y a six ans.", Etat.VRAI),
    ("Premier sevrage, sans complication.", Etat.FAUX),
    ("Sevrage hospitalier non compliqué.", Etat.FAUX),
    ("Pas d'antécédent de sevrage.", Etat.FAUX),
    ("Hospitalisé pour sevrage alcoolique programmé.", Etat.NA),  # sevrage actuel seul
    ("Consultation pour trouble du sommeil.", Etat.NA),
])
def test_sevrages_compliques(texte, attendu):
    assert val(texte, "sevrages_compliques") == attendu


# --- Alcool (#6) & tabac (#7) ---------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Alcool quotidien estimé à 12 verres.", Etat.VRAI),
    ("Conso OH chronique sévère.", Etat.VRAI),
    ("Pas d'alcool.", Etat.FAUX),
    ("Abstinence alcoolique maintenue depuis dix mois.", Etat.FAUX),
    ("Consultation de suivi diabète.", Etat.NA),
])
def test_alcool(texte, attendu):
    assert val(texte, "alcool") == attendu


@pytest.mark.parametrize("texte, attendu", [
    ("Tabagisme actif à 20 cig/j.", Etat.VRAI),
    ("Non fumeur.", Etat.FAUX),
    ("Ex-fumeur depuis le diagnostic.", Etat.FAUX),
    ("Tabac non.", Etat.FAUX),
])
def test_tabac(texte, attendu):
    assert val(texte, "tabac") == attendu


# --- Cannabis / THC / CBD (#8) --------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Usage régulier de cannabis.", "Cannabis"),
    ("Roule des joints au quotidien.", "Cannabis"),
    ("Utilise du CBD en gouttes le soir.", "CBD"),
    ("Cannabis à visée antalgique (THC).", "THC"),
    ("Pas de cannabis.", "NA"),
    ("Aucune substance mentionnée.", "NA"),
])
def test_cannabis(texte, attendu):
    assert val(texte, "cannabis") == attendu


# --- Cocaïne (#9) & voie (#10) --------------------------------------------- #
@pytest.mark.parametrize("texte, attendu_coc, attendu_voie", [
    ("Cocaïne par voie nasale lors de sorties.", Etat.VRAI, "nasale"),
    ("Cocaïne en injection intraveineuse.", Etat.VRAI, "intraveineuse"),
    ("Pas de cocaïne.", Etat.FAUX, "NA"),
    ("Patient sans particularité.", Etat.FAUX, "NA"),
])
def test_cocaine(texte, attendu_coc, attendu_voie):
    r = extraire_tout(texte)
    assert r["cocaine"].valeur == attendu_coc
    assert r["cocaine_voie"].valeur == attendu_voie


# --- Héroïne (#11) & quantité (#12) ---------------------------------------- #
@pytest.mark.parametrize("texte, attendu_her, attendu_q", [
    ("Héroïne IV, environ 0.5 g/jour.", Etat.VRAI, "0.5"),
    ("hero IV (env 1g/j d'après lui)", Etat.VRAI, "1.0"),
    ("Consommation d'héroïne fumée, environ 0.8 g par jour.", Etat.VRAI, "0.8"),
    ("Plus de consommation d'héroïne depuis huit mois.", Etat.FAUX, "NA"),
    ("Pas d'opiacés.", Etat.FAUX, "NA"),
])
def test_heroine(texte, attendu_her, attendu_q):
    r = extraire_tout(texte)
    assert r["heroine"].valeur == attendu_her
    assert r["heroine_quantite"].valeur == attendu_q


# --- Kétamine (#13) -------------------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Prises de kétamine en soirée.", Etat.VRAI),
    ("Usage ancien de kétamine, non actif.", Etat.FAUX),
    ("Kétamine rapportée par le passé, statut actuel incertain.", Etat.NA),
    ("Pas d'autre substance.", Etat.NA),
])
def test_ketamine(texte, attendu):
    assert val(texte, "ketamine") == attendu


# --- Traçabilité : confiance et preuve ------------------------------------- #
def test_preuve_et_confiance_renseignees():
    r = extraire_tout("Antécédent de delirium tremens lors d'un sevrage.")["sevrages_compliques"]
    assert r.valeur == Etat.VRAI
    assert 0.0 < r.confiance <= 1.0
    assert r.preuve and "delirium" in r.preuve
