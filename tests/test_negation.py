"""Tests de la brique de négation / logique 3 états (Phase 3)."""

import re

from cr_extract.normalisation import normaliser
from cr_extract.negation import est_nie, evaluer_terme

_ALCOOL = re.compile(r"(?<!\w)alcool\w*(?!\w)")


def _nie(phrase: str, terme: str = "alcool") -> bool:
    n = normaliser(phrase)
    m = re.search(re.escape(terme), n)
    assert m, f"terme {terme!r} absent de {n!r}"
    return est_nie(n, m.start(), m.end())


# --- Négations explicites avant le terme ----------------------------------- #
def test_negation_pas_de():
    assert _nie("pas d'alcool déclaré")


def test_negation_sans():
    assert _nie("sans alcool")


def test_negation_aucun():
    assert _nie("aucun usage d'alcool")


def test_negation_ne_pas_postpose():
    # « ne … pas » à cheval sur le terme.
    assert _nie("ne consomme pas d'alcool")


def test_reponse_negative_postposee():
    # « tabac non » : réponse négative juste après le terme.
    n = normaliser("Tabac non.")
    m = re.search("tabac", n)
    assert est_nie(n, m.start(), m.end())


# --- Affirmations qui ne doivent PAS être niées ---------------------------- #
def test_affirmation_simple():
    assert not _nie("consommation d'alcool quotidienne")


def test_anciennete_postposee_n_est_pas_negation():
    # « ancienne » après le terme = usage de longue date, toujours actif.
    assert not _nie("alcoolodépendance ancienne et sévère")


def test_ancien_avant_terme_nie():
    # « ancien » avant le terme (« ancien fumeur ») nie bien l'usage.
    assert _nie("ancien tabagisme sevré", terme="tabagisme")


def test_frontiere_parenthese():
    # Le « non » d'une incise fermée ne doit pas franchir la parenthèse.
    n = normaliser("héroïne fumée (quantité non chiffrée), cocaïne injectée")
    m = re.search("cocaine", n)
    assert not est_nie(n, m.start(), m.end())


# --- Décision 3 états : l'affirmation prime --------------------------------- #
def test_evaluer_terme_affirmation_prime_sur_negation():
    n = normaliser("alcool quotidien ; pas d'alcoolodépendance")
    assert evaluer_terme(n, _ALCOOL).valeur == "present"


def test_evaluer_terme_absent():
    assert evaluer_terme(normaliser("patient sans particularité"), _ALCOOL).valeur is None
