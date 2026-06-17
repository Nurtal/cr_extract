"""Interface en ligne de commande de CR Extract.

Deux sous-commandes :

- ``extraire`` : lit un CSV (colonne ``TEXTE``) et écrit un CSV structuré avec,
  pour chaque champ, la valeur extraite, son score de confiance et, en option,
  l'empan de preuve.
- ``evaluer`` : compare les prédictions à la vérité terrain (13 colonnes) et
  affiche le rapport d'exactitude par champ (option ``--confusions``).

Exemples
--------
    python -m cr_extract.cli extraire comptes_rendus_medicaux.csv -o sortie.csv
    python -m cr_extract.cli extraire entree.csv --preuves
    python -m cr_extract.cli evaluer comptes_rendus_medicaux.csv --confusions
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from cr_extract.chargement import charger_csv
from cr_extract.modele import CHAMPS
from cr_extract.pipeline import extraire_tout
from cr_extract.corpus import csv_vers_corpus, charger_corpus
from cr_extract.couverture import couverture_tags, rapport_couverture
from cr_extract.evaluation import (
    evaluer_corpus,
    evaluer_fichier,
    rapport_markdown,
    rapport_confusions,
)


def _charger_source(source: Path) -> list:
    """Charge un corpus JSON (dossier) ou un CSV annoté."""
    return charger_corpus(source) if Path(source).is_dir() else charger_csv(source)


def _commande_extraire(args: argparse.Namespace) -> int:
    crs = charger_csv(args.fichier)
    sortie = open(args.sortie, "w", encoding="utf-8", newline="") if args.sortie else sys.stdout
    try:
        entetes = ["index"]
        for champ in CHAMPS:
            entetes.append(champ.cle)
            entetes.append(f"{champ.cle}__confiance")
            if args.preuves:
                entetes.append(f"{champ.cle}__preuve")
        ecrivain = csv.writer(sortie)
        ecrivain.writerow(entetes)
        for cr in crs:
            resultats = extraire_tout(cr.texte)
            ligne = [cr.index]
            for champ in CHAMPS:
                r = resultats[champ.cle]
                ligne.append(r.valeur)
                ligne.append(f"{r.confiance:.2f}")
                if args.preuves:
                    ligne.append(r.preuve or "")
            ecrivain.writerow(ligne)
    finally:
        if sortie is not sys.stdout:
            sortie.close()
            print(f"{len(crs)} comptes rendus traités -> {args.sortie}", file=sys.stderr)
    return 0


def _commande_evaluer(args: argparse.Namespace) -> int:
    # On accepte indifféremment un CSV annoté ou un dossier de corpus JSON.
    if Path(args.source).is_dir():
        scores = evaluer_corpus(args.source)
    else:
        scores = evaluer_fichier(args.source)
    print(rapport_markdown(scores))
    if args.confusions:
        print()
        print(rapport_confusions(scores))
    return 0


def _commande_corpus(args: argparse.Namespace) -> int:
    chemins = csv_vers_corpus(args.fichier, args.sortie)
    print(f"{len(chemins)} comptes rendus écrits dans {args.sortie}/", file=sys.stderr)
    return 0


def _commande_couverture(args: argparse.Namespace) -> int:
    couverture = couverture_tags(_charger_source(args.source))
    print(rapport_couverture(couverture))
    return 0


def construire_parseur() -> argparse.ArgumentParser:
    parseur = argparse.ArgumentParser(
        prog="cr-extract",
        description="Extraction d'informations structurées de comptes rendus médicaux (regex).",
    )
    sous = parseur.add_subparsers(dest="commande", required=True)

    p_ex = sous.add_parser("extraire", help="produire un CSV structuré")
    p_ex.add_argument("fichier", type=Path, help="CSV d'entrée (colonne TEXTE)")
    p_ex.add_argument("-o", "--sortie", type=Path, default=None,
                      help="CSV de sortie (défaut : stdout)")
    p_ex.add_argument("--preuves", action="store_true",
                      help="inclure les empans de preuve pour audit")
    p_ex.set_defaults(fonction=_commande_extraire)

    p_ev = sous.add_parser("evaluer", help="comparer à la vérité terrain")
    p_ev.add_argument("source", type=Path,
                      help="CSV annoté (13 colonnes gold) ou dossier de corpus JSON")
    p_ev.add_argument("--confusions", action="store_true",
                      help="détailler les confusions par champ")
    p_ev.set_defaults(fonction=_commande_evaluer)

    p_co = sous.add_parser("corpus", help="générer un corpus JSON depuis un CSV")
    p_co.add_argument("fichier", type=Path, help="CSV annoté source")
    p_co.add_argument("-o", "--sortie", type=Path, default=Path("corpus"),
                      help="dossier de sortie (défaut : corpus/)")
    p_co.set_defaults(fonction=_commande_corpus)

    p_cv = sous.add_parser(
        "couverture",
        help="tags annotés couverts (ou non) par un extracteur",
    )
    p_cv.add_argument("source", type=Path,
                      help="CSV annoté ou dossier de corpus JSON")
    p_cv.set_defaults(fonction=_commande_couverture)

    return parseur


def main(argv: list[str] | None = None) -> int:
    args = construire_parseur().parse_args(argv)
    return args.fonction(args)


if __name__ == "__main__":
    raise SystemExit(main())
