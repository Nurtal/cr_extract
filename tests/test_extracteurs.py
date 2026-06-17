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


# --- Benzodiazépines + type ------------------------------------------------ #
@pytest.mark.parametrize("texte, presence, type_", [
    ("Dépendance aux benzodiazépines (zolpidem quotidien).", Etat.VRAI, "zolpidem"),
    ("Usage détourné de Lexomil.", Etat.VRAI, "bromazepam"),
    ("Mésusage de Xanax au long cours.", Etat.VRAI, "alprazolam"),
    ("Pas de benzodiazépines.", Etat.FAUX, "NA"),
    # Contexte thérapeutique : prescription de sevrage, pas une consommation.
    ("Sevrage sous oxazépam dégressif, bonne tolérance.", Etat.NA, "NA"),
    ("Traitement par diazépam en couverture du sevrage.", Etat.NA, "NA"),
    ("Consultation de suivi diabète.", Etat.NA, "NA"),
])
def test_benzodiazepines(texte, presence, type_):
    r = extraire_tout(texte)
    assert r["benzodiazepines"].valeur == presence
    assert r["benzodiazepine_type"].valeur == type_


# --- Hypnotiques + type ---------------------------------------------------- #
@pytest.mark.parametrize("texte, presence, type_", [
    ("Insomnie chronique, prise quotidienne de zopiclone (Imovane).", Etat.VRAI, "zopiclone"),
    ("Prend un somnifère chaque soir.", Etat.VRAI, "NA"),
    ("Usage d'hypnotique au long cours, doxylamine.", Etat.VRAI, "doxylamine"),
    ("Insomnie traitée par zolpidem.", Etat.VRAI, "zolpidem"),
    ("Pas d'hypnotique, pas de somnifère.", Etat.FAUX, "NA"),
    ("Consultation de suivi diabète.", Etat.NA, "NA"),
])
def test_hypnotiques(texte, presence, type_):
    r = extraire_tout(texte)
    assert r["hypnotiques"].valeur == presence
    assert r["hypnotique_type"].valeur == type_


# --- Addictolytiques + type ------------------------------------------------ #
@pytest.mark.parametrize("texte, presence, type_", [
    ("Maintien de l'abstinence alcoolique sous acamprosate (Aotal).", Etat.VRAI, "acamprosate"),
    ("Stabilisé sous buprénorphine (Subutex) depuis deux ans.", Etat.VRAI, "buprenorphine"),
    ("Substitution par méthadone bien suivie.", Etat.VRAI, "methadone"),
    ("Sevrage tabagique sous varénicline (Champix).", Etat.VRAI, "varenicline"),
    ("Mis sous traitement de substitution.", Etat.VRAI, "NA"),
    ("Pas de traitement de substitution actuellement.", Etat.FAUX, "NA"),
    # La naloxone (antidote d'overdose) n'est pas un addictolytique.
    ("Overdose aux opioïdes, naloxone aux urgences.", Etat.NA, "NA"),
    ("Consultation de suivi diabète.", Etat.NA, "NA"),
])
def test_addictolytique(texte, presence, type_):
    r = extraire_tout(texte)
    assert r["addictolytique"].valeur == presence
    assert r["addictolytique_type"].valeur == type_


# --- MDMA / LSD / amphétamines --------------------------------------------- #
@pytest.mark.parametrize("texte, champ, attendu", [
    ("Prise de MDMA (ecstasy) en soirée.", "mdma", Etat.VRAI),
    ("A pris de l'exta au festival.", "mdma", Etat.VRAI),
    ("Anxiété après prise de LSD.", "lsd", Etat.VRAI),
    ("Usage d'amphétamines (speed).", "amphetamines", Etat.VRAI),
    ("Consommation de crystal meth.", "amphetamines", Etat.VRAI),
    ("Pas de MDMA.", "mdma", Etat.FAUX),
    # « méthadone » ne doit pas déclencher amphétamines (méth ≠ meth).
    ("Substitution par méthadone.", "amphetamines", Etat.NA),
    ("Consultation de suivi diabète.", "lsd", Etat.NA),
])
def test_mdma_lsd_amphetamines(texte, champ, attendu):
    assert extraire_tout(texte)[champ].valeur == attendu


# --- Traitement de substitution (TSO) + type ------------------------------- #
@pytest.mark.parametrize("texte, presence, type_", [
    ("Substitution par méthadone bien suivie.", Etat.VRAI, "methadone"),
    ("Stabilisé sous buprénorphine (Subutex).", Etat.VRAI, "buprenorphine"),
    ("Renouvellement métha.", Etat.VRAI, "methadone"),
    ("Lien CSAPA et TSO.", Etat.VRAI, "NA"),
    ("Pas de ttt substitution actuellement.", Etat.FAUX, "NA"),
    # Substitution nicotinique (tabac) : ce n'est pas un TSO.
    ("Sevrage tabagique sous substitution nicotinique.", Etat.NA, "NA"),
    # Acamprosate est un addictolytique mais pas une substitution opiacée.
    ("Maintien de l'abstinence sous acamprosate.", Etat.NA, "NA"),
])
def test_traitement_substitution(texte, presence, type_):
    r = extraire_tout(texte)
    assert r["traitement_substitution"].valeur == presence
    assert r["traitement_substitution_type"].valeur == type_


# --- Grossesse ------------------------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Patiente enceinte de 18 semaines.", Etat.VRAI),
    ("Patiente gestante, suivi obstétrical.", Etat.VRAI),
    ("Test de grossesse négatif.", Etat.FAUX),
    ("Patiente non enceinte.", Etat.FAUX),
    # Antécédents / projet / repère temporel : pas une grossesse en cours.
    ("Deux grossesses antérieures, trois enfants.", Etat.NA),
    ("Consultation pour sevrage tabac avant grossesse.", Etat.NA),
    ("Désir de grossesse exprimé.", Etat.NA),
    ("Consultation de suivi diabète.", Etat.NA),
])
def test_grossesse(texte, attendu):
    assert extraire_tout(texte)["grossesse"].valeur == attendu


# --- Hépatopathie ---------------------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Cirrhose alcoolique avec varices œsophagiennes.", Etat.VRAI),
    ("Hospitalisée pour bilan d'une cytolyse hépatique.", Etat.VRAI),
    ("Hépatopathie alcoolique.", Etat.VRAI),
    ("Hépatite C chronique.", Etat.VRAI),
    ("Bilan hépatique normal, pas de cirrhose.", Etat.FAUX),
    ("Foie normal à l'échographie.", Etat.FAUX),
    # « bilan hépatique » seul = examen, pas une maladie.
    ("Bilan hépatique demandé.", Etat.NA),
    ("Consultation de suivi diabète.", Etat.NA),
])
def test_hepatopathie(texte, attendu):
    assert extraire_tout(texte)["hepatopathie"].valeur == attendu


# --- Suivi hépato-gastro-entérologie --------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Compte rendu - Hépato-Gastro-Entérologie.", Etat.VRAI),
    ("Suivi en hépato-gastro-entérologie programmé.", Etat.VRAI),
    ("Adressé à l'hépatologue.", Etat.VRAI),
    ("Avis gastro-entérologique demandé.", Etat.VRAI),
    ("Lien CSAPA et suivi HGE.", Etat.VRAI),
    ("Pas de suivi gastro-entérologique.", Etat.FAUX),
    # « digestive » (acte/symptôme) n'est pas un suivi HGE.
    ("Hospitalisation en chirurgie digestive.", Etat.NA),
    ("Hémorragie digestive sur varices œsophagiennes.", Etat.NA),
    ("Consultation de suivi diabète.", Etat.NA),
])
def test_suivi_hepato_gastro(texte, attendu):
    assert extraire_tout(texte)["suivi_hepato_gastro"].valeur == attendu


# --- Pancréatite ----------------------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Pancréatite aiguë d'origine éthylique.", Etat.VRAI),
    ("Pancréatite chronique calcifiante.", Etat.VRAI),
    ("Lipase normale, pas de pancréatite.", Etat.FAUX),
    # « pancréas » seul (organe / autre contexte) ne compte pas.
    ("Adénocarcinome du pancréas.", Etat.NA),
    ("Consultation de suivi diabète.", Etat.NA),
])
def test_pancreatite(texte, attendu):
    assert extraire_tout(texte)["pancreatite"].valeur == attendu


# --- Problèmes cardiovasculaires ------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("AVC ischémique, unité neurovasculaire.", Etat.VRAI),
    ("Suivi insuffisance cardiaque.", Etat.VRAI),
    ("Admis pour endocardite.", Etat.VRAI),
    ("Antécédents cardiovasculaires multiples.", Etat.VRAI),
    ("Pas d'antécédent cardiovasculaire.", Etat.FAUX),
    # Symptômes transitoires / bilan : pas une pathologie CV avérée.
    ("Palpitations après prise de THC.", Etat.NA),
    ("Tachycardie après prise de MDMA.", Etat.NA),
    ("Évaluation cardiovasculaire proposée.", Etat.NA),
    ("Douleur thoracique, finalement reflux.", Etat.NA),
])
def test_cardiovasculaire(texte, attendu):
    assert extraire_tout(texte)["cardiovasculaire"].valeur == attendu


# --- BPCO ------------------------------------------------------------------ #
@pytest.mark.parametrize("texte, attendu", [
    ("BPCO sévère post-tabagique.", Etat.VRAI),
    ("Bronchopneumopathie chronique obstructive stade II.", Etat.VRAI),
    ("Bronchite chronique.", Etat.VRAI),
    ("Emphysème pulmonaire.", Etat.VRAI),
    ("EFR normales, pas de BPCO.", Etat.FAUX),
    # « pneumopathie » (pneumonie aiguë) n'est pas une BPCO.
    ("Admis pour une pneumopathie sur terrain précaire.", Etat.NA),
    ("Consultation de suivi diabète.", Etat.NA),
])
def test_bpco(texte, attendu):
    assert extraire_tout(texte)["bpco"].valeur == attendu


# --- Emphysème ------------------------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Emphysème pulmonaire sévère.", Etat.VRAI),
    ("Poumons emphysémateux.", Etat.VRAI),
    ("Pas d'emphysème.", Etat.FAUX),
    ("Consultation de suivi diabète.", Etat.NA),
])
def test_emphyseme(texte, attendu):
    assert extraire_tout(texte)["emphyseme"].valeur == attendu


def test_emphyseme_recoupe_bpco():
    # L'emphysème pulmonaire active aussi le champ BPCO (axes liés).
    r = extraire_tout("Emphysème pulmonaire sévère.")
    assert r["emphyseme"].valeur == Etat.VRAI
    assert r["bpco"].valeur == Etat.VRAI


# --- Diabète --------------------------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Diabète de type 2 déséquilibré.", Etat.VRAI),
    ("Patient diabétique insulinodépendant.", Etat.VRAI),
    ("Consultation de suivi diabète.", Etat.VRAI),
    ("Bilan métabolique : pas de diabète.", Etat.FAUX),
    ("Patient non diabétique.", Etat.FAUX),
    # Une glycémie isolée n'est pas un diabète.
    ("Glycémie à 1.1 g/L.", Etat.NA),
    ("Consultation de suivi hypertension.", Etat.NA),
])
def test_diabete(texte, attendu):
    assert extraire_tout(texte)["diabete"].valeur == attendu


# --- Troubles cognitifs ---------------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Troubles cognitifs sévères.", Etat.VRAI),
    ("Syndrome de Korsakoff.", Etat.VRAI),
    ("Démence débutante.", Etat.VRAI),
    ("Troubles mnésiques.", Etat.VRAI),
    ("Pas de troubles cognitifs.", Etat.FAUX),
    ("Fonctions cognitives normales.", Etat.FAUX),
    # « risques cognitifs » (information) / confusion aiguë : pas un trouble avéré.
    ("Information sur les risques urologiques et cognitifs.", Etat.NA),
    ("Syndrome confusionnel fébrile.", Etat.NA),
    ("Consultation de suivi diabète.", Etat.NA),
])
def test_troubles_cognitifs(texte, attendu):
    assert extraire_tout(texte)["troubles_cognitifs"].valeur == attendu


# --- Dépression / épisode dépressif ---------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Épisode dépressif sévère.", Etat.VRAI),
    ("Syndrome anxio-dépressif.", Etat.VRAI),
    ("Dépression caractérisée.", Etat.VRAI),
    ("Pas de syndrome dépressif.", Etat.FAUX),
    # Anxiété / humeur / médicament : pas une dépression avérée.
    ("Crise d'angoisse.", Etat.NA),
    ("Décompensation thymique sur fond de polyconsommation.", Etat.NA),
    ("Consulte pour gérer son anxiété.", Etat.NA),
    ("Sous antidépresseur.", Etat.NA),
])
def test_depression(texte, attendu):
    assert extraire_tout(texte)["depression"].valeur == attendu


# --- Troubles anxieux ------------------------------------------------------ #
@pytest.mark.parametrize("texte, attendu", [
    ("Trouble anxieux généralisé.", Etat.VRAI),
    ("Crise d'angoisse.", Etat.VRAI),
    ("Anxiété aiguë après prise de MDMA.", Etat.VRAI),
    ("Syndrome anxio-dépressif.", Etat.VRAI),
    ("Pas de trouble anxieux.", Etat.FAUX),
    # « anxiolytique » (médicament) n'est pas un trouble anxieux.
    ("Sous anxiolytique le soir.", Etat.NA),
    ("Consultation de suivi diabète.", Etat.NA),
])
def test_troubles_anxieux(texte, attendu):
    assert extraire_tout(texte)["troubles_anxieux"].valeur == attendu


def test_anxio_depressif_active_anxieux_et_depression():
    r = extraire_tout("Syndrome anxio-dépressif réactionnel.")
    assert r["troubles_anxieux"].valeur == Etat.VRAI
    assert r["depression"].valeur == Etat.VRAI


# --- Troubles bipolaires --------------------------------------------------- #
@pytest.mark.parametrize("texte, attendu", [
    ("Trouble bipolaire de type I.", Etat.VRAI),
    ("Patient bipolaire stabilisé.", Etat.VRAI),
    ("Épisode maniaque avec agitation.", Etat.VRAI),
    ("Psychose maniaco-dépressive.", Etat.VRAI),
    ("Cyclothymie.", Etat.VRAI),
    ("Pas de trouble bipolaire.", Etat.FAUX),
    # « décompensation thymique » n'est pas spécifiquement bipolaire.
    ("Décompensation thymique.", Etat.NA),
    ("Consultation de suivi diabète.", Etat.NA),
])
def test_troubles_bipolaires(texte, attendu):
    assert extraire_tout(texte)["troubles_bipolaires"].valeur == attendu


# --- Traçabilité : confiance et preuve ------------------------------------- #
def test_preuve_et_confiance_renseignees():
    r = extraire_tout("Antécédent de delirium tremens lors d'un sevrage.")["sevrages_compliques"]
    assert r.valeur == Etat.VRAI
    assert 0.0 < r.confiance <= 1.0
    assert r.preuve and "delirium" in r.preuve
