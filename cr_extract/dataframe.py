"""Détection d'items sur un DataFrame (polars ou pandas).

Expose :func:`detecter`, qui enrichit un DataFrame contenant une colonne de texte
libre d'une colonne par item demandé, indiquant la présence / l'absence de
l'item. La sortie est toujours un :class:`polars.DataFrame` (copie de l'entrée).

L'encodage des colonnes ajoutées suit le type du champ :

- champ booléen  -> ``True`` / ``False`` / ``null`` (NA = non abordé) ;
- champ catégoriel -> libellé de la catégorie / ``null`` ;
- champ numérique  -> flottant / ``null``.

``polars`` est requis ; ``pandas`` ne l'est que si l'entrée est un DataFrame
pandas (importé paresseusement).
"""

from __future__ import annotations

from typing import Iterable

from cr_extract.modele import (
    CHAMPS_PAR_CLE,
    Etat,
    TYPE_BOOLEEN,
    TYPE_NUMERIQUE,
)
from cr_extract.normalisation import normaliser
from cr_extract.extracteurs import extracteurs_disponibles

COLONNE_TEXTE_DEFAUT = "TEXTE"


def detecter(
    df,
    items: Iterable[str],
    colonne_texte: str = COLONNE_TEXTE_DEFAUT,
    prefixe: str = "",
):
    """Détecte des items dans la colonne texte d'un DataFrame.

    Parameters
    ----------
    df :
        DataFrame d'entrée, ``polars`` ou ``pandas``. Il n'est pas modifié : une
        copie polars est renvoyée.
    items :
        Clés des items à détecter (voir :data:`cr_extract.modele.CHAMPS_PAR_CLE`,
        p. ex. ``"alcool"``, ``"tabac"``, ``"cocaine"``, ``"cannabis"``…).
    colonne_texte :
        Nom de la colonne contenant le texte libre (défaut : ``"TEXTE"``).
    prefixe :
        Préfixe optionnel des colonnes ajoutées (p. ex. ``"item_"``).

    Returns
    -------
    polars.DataFrame
        Copie de ``df`` (en polars) augmentée d'une colonne ``prefixe + item``
        par item demandé.

    Raises
    ------
    ValueError
        Si la colonne texte est absente, ou si un item est inconnu.
    """
    import polars as pl

    pdf = _vers_polars(df)

    if colonne_texte not in pdf.columns:
        raise ValueError(
            f"Colonne texte '{colonne_texte}' absente ; "
            f"colonnes disponibles : {pdf.columns}"
        )

    items = list(items)
    extracteurs = extracteurs_disponibles()
    inconnus = [i for i in items if i not in extracteurs]
    if inconnus:
        raise ValueError(
            f"Items inconnus : {inconnus}. "
            f"Items disponibles : {sorted(extracteurs)}"
        )

    # Une seule normalisation par ligne, puis tous les extracteurs demandés.
    textes = pdf.get_column(colonne_texte).to_list()
    valeurs: dict[str, list] = {item: [] for item in items}
    for texte in textes:
        texte = texte if isinstance(texte, str) else ""
        texte_normalise = normaliser(texte)
        for item in items:
            resultat = extracteurs[item].extraire(texte_normalise, texte)
            valeurs[item].append(_convertir(resultat.valeur, CHAMPS_PAR_CLE[item].type_))

    return pdf.with_columns(
        [pl.Series(prefixe + item, valeurs[item]) for item in items]
    )


def _convertir(valeur: str, type_champ: str):
    """Traduit la valeur canonique (chaîne) vers un type natif polars-friendly."""
    if valeur == Etat.NA:
        return None
    if type_champ == TYPE_BOOLEEN:
        return valeur == Etat.VRAI
    if type_champ == TYPE_NUMERIQUE:
        return float(valeur)
    return valeur


def _vers_polars(df):
    """Renvoie une copie polars du DataFrame d'entrée (polars ou pandas)."""
    import polars as pl

    if isinstance(df, pl.DataFrame):
        return df.clone()

    module_racine = type(df).__module__.split(".")[0]
    if module_racine == "pandas":
        # Construction colonne par colonne (listes Python) pour ne pas dépendre
        # de pyarrow, requis par ``pl.from_pandas`` sur les colonnes texte.
        return pl.DataFrame({str(col): df[col].tolist() for col in df.columns})

    raise TypeError(
        "df doit être un DataFrame polars ou pandas, "
        f"reçu : {type(df).__module__}.{type(df).__name__}"
    )
