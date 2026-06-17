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
Aucune dépendance d'exécution (bibliothèque standard uniquement). Pour les tests :

```bash
pip install -r requirements.txt   # pytest
```

## Guide d'utilisation

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

### 3. En Python

```python
from cr_extract import extraire_tout

resultats = extraire_tout("Patient marié, en activité. Tabac actif. Pas d'alcool.")

r = resultats["alcool"]
print(r.valeur)      # False  (négation explicite « pas d'alcool »)
print(r.confiance)   # 1.0
print(r.preuve)      # empan de texte ayant motivé la décision

resultats["situation_conjugale"].valeur   # "en couple"
resultats["tabac"].valeur                  # True
```

Pour itérer sur un fichier complet avec accès aux annotations de référence :

```python
from cr_extract import charger_csv, extraire_tout

for cr in charger_csv("comptes_rendus_medicaux.csv"):
    predictions = extraire_tout(cr.texte)
    # cr.gold contient les valeurs de référence par clé de champ
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
