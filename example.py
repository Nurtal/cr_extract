"""Exemple d'utilisation de CR Extract.

À lancer depuis la racine du dépôt, après installation du package
(``pip install .``) ou des dépendances (``pip install -r requirements.txt``) :

    python example.py
"""

import polars as pl

from cr_extract import detecter, extraire_tout


# Quelques comptes rendus fictifs (texte libre).
COMPTES_RENDUS = [
    "Patient marié, en activité. Tabac actif. Pas d'alcool. "
    "Cocaïne par voie nasale lors de sorties festives.",
    "Homme SDF, célibataire. Héroïne en intraveineuse, environ 0.5 g/jour. "
    "Pas de cannabis. Tabac.",
    "Consultation de suivi diabète. Aucune consommation, patient stable.",
    "Sans emploi, hébergé. Crack fumé à la pipe, plusieurs prises par jour. "
    "Pas d'héroïne.",
]


def exemple_dataframe() -> None:
    """Usage recommandé : enrichir un DataFrame avec une colonne par item."""
    df = pl.DataFrame({"TEXTE": COMPTES_RENDUS})

    # On choisit les items à détecter (cf. README pour la liste complète).
    items = ["alcool", "tabac", "cocaine", "crack", "crack_voie", "heroine",
             "heroine_quantite", "sdf", "situation_conjugale"]

    resultat = detecter(df, items=items)

    print("=== detecter() : DataFrame enrichi ===")
    with pl.Config(tbl_cols=-1, fmt_str_lengths=40):
        print(resultat)
    print()

    # Le résultat est un DataFrame polars classique : on peut le filtrer.
    usagers_cocaine = resultat.filter(pl.col("cocaine"))
    print(f"{usagers_cocaine.height} compte(s) rendu(s) avec usage de cocaïne.\n")


def exemple_extraction_unitaire() -> None:
    """Extraction détaillée d'un seul texte : valeur + confiance + preuve."""
    resultats = extraire_tout(COMPTES_RENDUS[0])

    print("=== extraire_tout() : détail d'un compte rendu ===")
    for cle in ("situation_conjugale", "alcool", "tabac", "cocaine", "cocaine_voie"):
        r = resultats[cle]
        preuve = f" (preuve : « {r.preuve} »)" if r.preuve else ""
        print(f"  {cle:24} = {r.valeur:<14} confiance={r.confiance:.2f}{preuve}")
    print()


if __name__ == "__main__":
    exemple_dataframe()
    exemple_extraction_unitaire()
