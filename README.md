# CR Extract

## Description
Extraction d'informations structurées à partir de comptes rendus médicaux non
structurés (addictologie / psychiatrie, texte libre en français).
Toutes les données utilisées ici sont **fictives**.

Tous les extracteurs reposent sur des **combinaisons de regex** ; un **score de
confiance** accompagne chaque décision, surtout utile pour les champs difficiles.
Chaque décision est tracée par une **preuve** (l'empan de texte qui l'a
déclenchée), pour l'audit clinique.

## Les 13 champs extraits

| # | Clé interne | Valeurs possibles |
|---|-------------|-------------------|
| 1 | `situation_conjugale` | `en couple` / `célibataire` / `NA` |
| 2 | `situation_professionnelle` | `actif` / `inactif` / `NA` |
| 3 | `sdf` | `True` / `False` / `NA` |
| 4 | `protection_juridique` | `curatelle` / `tutelle` / `NA` |
| 5 | `sevrages_compliques` | `True` / `False` / `NA` |
| 6 | `alcool` | `True` / `False` / `NA` |
| 7 | `tabac` | `True` / `False` / `NA` |
| 8 | `cannabis` | `Cannabis` / `THC` / `CBD` / `NA` |
| 9 | `cocaine` | `True` / `False` |
| 10 | `cocaine_voie` | `nasale` / `intraveineuse` / `NA` |
| 11 | `heroine` | `True` / `False` |
| 12 | `heroine_quantite` | nombre (g/j) / `NA` |
| 13 | `ketamine` | `True` / `False` / `NA` |

**Distinction clé** : `False` (négation explicite, « pas d'alcool ») ≠ `NA`
(sujet non abordé dans le compte rendu). Voir [`ROADMAP.md`](ROADMAP.md) pour le
détail des champs et des phases.

## Installation

Le projet s'installe comme un package Python (sans passer par PyPI) et s'utilise
ensuite depuis n'importe quel autre code : `import cr_extract` fonctionne depuis
n'importe quel dossier, et la commande `cr-extract` est ajoutée au PATH.

### Depuis un clone du dépôt

```bash
git clone git@github.com:Nurtal/cr_extract.git
cd cr_extract

pip install .                 # installation classique (copie figée)
pip install ".[pandas]"       # + support des DataFrames pandas en entrée
pip install -e ".[dev]"       # mode éditable + pytest et pandas (développement)
```

Le mode **éditable** (`-e`) fait pointer le package vers les sources : les
modifications du code sont prises en compte sans réinstaller — pratique pour
itérer en local.

### Directement depuis Git (sans cloner)

```bash
pip install "git+ssh://git@github.com/Nurtal/cr_extract.git"
# ou une version/tag précis :
pip install "git+ssh://git@github.com/Nurtal/cr_extract.git@v0.2.1"
```

Seule dépendance d'exécution : `polars` (installée automatiquement). `pandas`
n'est requis que si vous passez un DataFrame pandas en entrée.

## Guide d'utilisation

> 💡 Un exemple complet et exécutable est fourni dans
> [`example.py`](example.py) (`python example.py`).

### 1. Extraire — produire un CSV structuré

```bash
# Sortie sur un fichier
python -m cr_extract.cli extraire comptes_rendus_medicaux.csv -o sortie.csv

# Sortie sur la console
python -m cr_extract.cli extraire entree.csv

# Inclure les empans de preuve (audit)
python -m cr_extract.cli extraire entree.csv --preuves -o sortie.csv
```

Le CSV d'entrée doit contenir au moins une colonne `TEXTE`. Le CSV de sortie
comporte, par compte rendu (ligne) et par champ :

- `<champ>` : la valeur extraite ;
- `<champ>__confiance` : le score de confiance dans `[0, 1]` ;
- `<champ>__preuve` : l'empan déclencheur (uniquement avec `--preuves`).

### 2. Évaluer — comparer à la vérité terrain

Si le CSV contient aussi les 13 colonnes de référence (gold), on mesure la
qualité des extracteurs :

```bash
python -m cr_extract.cli evaluer comptes_rendus_medicaux.csv

# Avec le détail des confusions (gold -> prédiction) par champ
python -m cr_extract.cli evaluer comptes_rendus_medicaux.csv --confusions
```

Le rapport donne l'accuracy par champ et l'accuracy globale, et — avec
`--confusions` — les confusions les plus fréquentes (notamment `False` vs `NA`),
pour piloter le raffinage des regex.

### 3. Sur un DataFrame (polars ou pandas) — usage recommandé en intégration

`detecter` prend un DataFrame contenant une colonne de texte et la liste des
items à détecter, et renvoie une **copie polars** enrichie d'une colonne par
item :

```python
import polars as pl
from cr_extract import detecter

df = pl.DataFrame({"TEXTE": [
    "Patient marié. Tabac actif. Pas d'alcool. Cocaïne nasale.",
    "SDF. Héroïne IV environ 0.5 g/jour. Pas de cannabis.",
]})

resultat = detecter(df, items=["alcool", "tabac", "cocaine", "sdf", "heroine_quantite"])
print(resultat)
```

```
┌─────────────────────┬────────┬───────┬─────────┬───────┬──────────────────┐
│ TEXTE               ┆ alcool ┆ tabac ┆ cocaine ┆ sdf   ┆ heroine_quantite │
│ str                 ┆ bool   ┆ bool  ┆ bool    ┆ bool  ┆ f64              │
╞═════════════════════╪════════╪═══════╪═════════╪═══════╪══════════════════╡
│ Patient marié. …    ┆ false  ┆ true  ┆ true    ┆ false ┆ null             │
│ SDF. Héroïne IV …   ┆ null   ┆ null  ┆ false   ┆ true  ┆ 0.5              │
└─────────────────────┴────────┴───────┴─────────┴───────┴──────────────────┘
```

- L'entrée peut être un DataFrame **polars** ou **pandas** ; le DataFrame
  d'origine n'est pas modifié.
- Encodage des colonnes ajoutées selon le type d'item :
  - booléen → `True` (présent) / `False` (nié explicitement) / `null` (non abordé) ;
  - catégoriel → libellé (`"en couple"`, `"Cannabis"`, `"nasale"`…) / `null` ;
  - numérique (`heroine_quantite`) → flottant en g/j / `null`.
- Options : `colonne_texte=` (défaut `"TEXTE"`), `prefixe=` (préfixe des
  colonnes ajoutées, p. ex. `"item_"`).

Items disponibles : `situation_conjugale`, `situation_professionnelle`, `sdf`,
`protection_juridique`, `sevrages_compliques`, `alcool`, `tabac`, `cannabis`,
`cocaine`, `cocaine_voie`, `heroine`, `heroine_quantite`, `ketamine`.

Voir [`example.py`](example.py) pour un script complet (détection sur DataFrame
puis filtrage du résultat).

### 4. Extraction unitaire en Python

```python
from cr_extract import extraire_tout

resultats = extraire_tout("Patient marié, en activité. Tabac actif. Pas d'alcool.")

r = resultats["alcool"]
print(r.valeur)      # False  (négation explicite « pas d'alcool »)
print(r.confiance)   # 1.0
print(r.preuve)      # empan de texte ayant motivé la décision
```

## Score de confiance

La confiance vaut `1.0` sur les marqueurs explicites et est abaissée quand la
décision est ambiguë ou implicite :

- conflit actif/inactif → `0.6` ;
- SDF déduit par défaut (logement présumé) → `0.6` ;
- quantité d'héroïne (extraction numérique) → `0.7`.

On privilégie un `NA` prudent quand aucun signal fiable n'est trouvé, plutôt
qu'un faux positif.

## Architecture

```
cr_extract/
├── modele.py          # catalogue des 13 champs, ResultatExtraction, interface
├── normalisation.py   # minuscules / sans accents (regex) ; texte d'origine préservé
├── chargement.py      # lecture CSV (utf-8-sig, champs multi-lignes)
├── negation.py        # brique transverse : négation + logique 3 états (True/False/NA)
├── extracteurs/       # un module par famille de champs (registre auto-enregistré)
│   ├── conjugal.py · professionnel.py · logement.py
│   ├── juridique.py · sevrage.py · substances.py
├── pipeline.py        # applique les 13 extracteurs à un texte
├── dataframe.py       # detecter() : enrichit un DataFrame polars/pandas
├── evaluation.py      # accuracy / matrice de confusion vs gold
└── cli.py
```

Point clé : la distinction **`False`** vs **`NA`** est modélisée dans
`negation.py` et réutilisée par tous les champs booléens.

## Tests & performance

```bash
python -m pytest        # 87 tests
```

Sur le CSV de référence (100 comptes rendus) : **accuracy globale 98,2 %**
(1277/1300). Tous les champs dépassent les cibles de la ROADMAP
(≥ 90 % faciles, ≥ 75 % difficiles).
