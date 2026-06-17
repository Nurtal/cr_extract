# ROADMAP — CR Extract

Extraction d'informations structurées à partir de comptes rendus médicaux non
structurés, **par combinaisons de regex** (+ score de confiance pour les cas
difficiles). Données 100 % fictives.

> **État d'avancement (Phases 1 → 6 réalisées).** Pipeline complet,
> 13 extracteurs, harnais d'évaluation et CLI. **Accuracy globale : 98,2 %**
> (1277/1300) sur le CSV de référence ; tous les champs dépassent les cibles
> (≥ 90 % faciles, ≥ 75 % difficiles). Les erreurs résiduelles relèvent
> majoritairement d'annotations contradictoires de la vérité terrain (textes
> quasi identiques étiquetés différemment, notamment `False` vs `NA`).
> Mesurer : `python -m cr_extract.cli evaluer comptes_rendus_medicaux.csv`.

---

## 0. Cadre & contraintes

- **Entrée** : colonne `TEXTE` du CSV (texte libre FR, addictologie/psychiatrie).
- **Sortie** : 13 champs structurés (voir tableau ci-dessous).
- **Méthode imposée** : regex uniquement (pas de ML), score de confiance optionnel.
- **Vérité terrain** : les 13 colonnes du CSV servent de gold labels pour l'évaluation.
- **Langue du code/docs** : français (cohérence avec le README).

### Les 13 champs cibles

| # | Champ | Type | Valeurs | Difficulté |
|---|-------|------|---------|------------|
| 1 | Célibataire / en couple | catégoriel | `en couple` / `célibataire` / `NA` | moyenne |
| 2 | Situation professionnelle | catégoriel | `actif` / `inactif` / `NA` | élevée |
| 3 | SDF / absence de logement | booléen 3-états | `True` / `False` / `NA` | moyenne |
| 4 | Curatelle / Tutelle | catégoriel | `curatelle` / `tutelle` / `NA` | faible |
| 5 | Antécédents sevrages compliqués | booléen 3-états | `True` / `False` / `NA` | élevée |
| 6 | Consommation alcool | booléen 3-états | `True` / `False` / `NA` | moyenne |
| 7 | Consommation tabac | booléen 3-états | `True` / `False` / `NA` | moyenne |
| 8 | Cannabis / THC / CBD | catégoriel | `Cannabis` / `THC` / `CBD` / `NA` | moyenne |
| 9 | Cocaïne | booléen | `True` / `False` | moyenne |
| 10 | Cocaïne – voie d'administration | catégoriel | `nasale` / `intraveineuse` / `NA` | faible |
| 11 | Héroïne | booléen | `True` / `False` | moyenne |
| 12 | Héroïne – quantité | numérique | `0.3`–`1.2` (g/j) / `NA` | élevée |
| 13 | Kétamine | booléen 3-états | `True` / `False` / `NA` | faible |

**Distinction clé à modéliser partout** : `False` (négation explicite, ex. « pas
d'alcool ») ≠ `NA` (sujet non abordé dans le CR).

---

## Phase 1 — Socle technique

**But** : pouvoir charger les données et lancer une évaluation, même avec des
extracteurs vides.

- [x] Structure du projet (package `cr_extract/`, `tests/`, `requirements.txt`,
      `.gitignore` excluant `venv/`).
- [x] Chargement CSV robuste (`utf-8-sig` pour le BOM, gestion des champs
      multi-lignes — déjà géré par le module `csv`).
- [x] Modèle de résultat commun : `ResultatExtraction(valeur, confiance, preuve)`
      où `preuve` = empan/texte ayant déclenché le match (traçabilité).
- [x] Interface `Extracteur` (une classe/fonction par champ, signature unifiée).
- [x] Normalisation du texte en amont : minuscules, gestion des accents pour les
      regex, mais **conservation** du texte d'origine pour la preuve.

## Phase 2 — Extracteurs « faciles » (validation de l'approche)

Champs à vocabulaire fermé et marqueurs explicites — sert de preuve de concept.

- [x] **Curatelle / Tutelle** (#4) : `curatelle`, `tutelle`, gestion de la négation
      (« pas de mesure de protection » → `NA`).
- [x] **Cocaïne – voie** (#10) : `nasale|sniff`, `IV|intraveineuse|injection`.
- [x] **Kétamine** (#13), **Cocaïne** (#9), **Héroïne** (#11) : présence + négation.
- [x] **Cannabis / THC / CBD** (#8) : choix de la sous-catégorie selon le terme.

## Phase 3 — Gestion de la négation & des 3 états (cœur du sujet)

Brique transverse réutilisée par les champs booléens (#3, #5, #6, #7, #13…).

- [x] Lexique de négation FR : `pas de`, `aucun`, `nie`, `absence de`, `sans`,
      `dénie`, `ne … pas`, abréviations (`0`, `–`).
- [x] Fenêtre de proximité négation↔terme (n caractères/tokens) pour rattacher
      la négation au bon item.
- [x] Logique 3 états : terme + contexte positif → `True` ; terme + négation →
      `False` ; terme absent → `NA`.
- [x] Tests unitaires dédiés négation (cas « pas d'autre toxique », « nie tout
      usage d'opiacés ou de cocaïne »).

## Phase 4 — Extracteurs « difficiles » + score de confiance

- [x] **Situation professionnelle** (#2) : `actif` (emploi, activité maintenue,
      profession citée) vs `inactif` (chômage, arrêt de travail, AAH, retraité,
      sans emploi). Synonymie riche → **score de confiance**.
- [x] **Antécédents sevrages compliqués** (#5) : sevrage **antérieur** +
      complication (`delirium tremens`, `crises convulsives`, `réanimation`) ;
      distinguer du sevrage actuel/programmé. → **score de confiance**.
- [x] **Situation conjugale** (#1) : `marié·e`, `en couple`, `conjoint` vs
      `célibataire`, `séparé`, `divorcé`, `seul`.
- [x] **Héroïne – quantité** (#12) : extraction numérique (`0.5 g/j`, « un demi
      gramme »…), normalisation des unités vers g/j, gestion virgule décimale.
- [x] **SDF** (#3) : `SDF`, `sans domicile`, `pas de logement stable`, `à la rue`
      vs logement mentionné.
- [x] Calibration : émettre `NA` plutôt qu'un faux positif quand confiance < seuil.

## Phase 5 — Évaluation & qualité

- [x] Harnais d'éval : prédiction vs gold, **accuracy par champ** + matrice de
      confusion (notamment `False` vs `NA`).
- [x] Rapport global (CSV/markdown) + identification des lignes en échec.
- [x] Objectif chiffré par champ (ex. ≥ 90 % sur les champs faciles, ≥ 75 % sur
      les difficiles) — à ajuster après première mesure (baseline).
- [x] Suite de tests unitaires par extracteur (cas limites issus du CSV).
- [x] Itération : analyse d'erreurs → raffinage des regex → re-mesure.

## Phase 6 — Industrialisation (optionnel)

- [x] CLI : `cr-extract <fichier.csv>` → CSV structuré + colonnes de confiance.
- [x] Export des preuves (empans) pour audit clinique.
- [x] Documentation d'usage dans le README + exemples.

---

## Architecture cible (proposition)

```
cr_extract/
├── __init__.py
├── modele.py          # ResultatExtraction, types de champs
├── chargement.py      # lecture CSV (utf-8-sig)
├── negation.py        # brique transverse négation / 3 états (Phase 3)
├── extracteurs/
│   ├── __init__.py    # registre {nom_champ: extracteur}
│   ├── conjugal.py
│   ├── professionnel.py
│   ├── logement.py
│   ├── juridique.py
│   ├── sevrage.py
│   └── substances.py  # alcool, tabac, cannabis, cocaïne, héroïne, kétamine
├── evaluation.py      # accuracy/matrice de confusion vs gold
└── cli.py
tests/
└── test_*.py
```

## Décisions tranchées (mise en œuvre actuelle)

1. **Stockage des regex** : **en dur dans le code Python**, regroupées en tête de
   chaque module d'extracteur (lisibilité + accès direct à la logique de
   décision). L'externalisation YAML reste une évolution possible si le besoin
   d'itération sans code se confirme.
2. **Score de confiance** : présent **sur tous les champs**, mais réellement
   discriminant sur les « difficiles » — confiance abaissée en cas d'ambiguïté
   (conflit actif/inactif → 0.6 ; SDF déduit par défaut → 0.6 ; quantité
   héroïne → 0.7) et maximale (1.0) sur les marqueurs explicites.
3. **Seuils** : on privilégie un **`NA` prudent** lorsqu'aucun signal fiable
   n'est trouvé (champs catégoriels/3 états), conformément à la distinction
   `False`/`NA`. Les deux champs strictement booléens (#9 cocaïne, #11 héroïne)
   font exception : absence de mention = `False` (convention de la vérité
   terrain).

## Pistes d'amélioration ultérieures

- Externalisation des lexiques (YAML par champ) pour itérer sans toucher au code.
- Fenêtre de proximité pondérée (distance négation↔terme) plutôt que binaire.
- Désambiguïsation `False`/`NA` sur SDF et sevrages (principale source d'erreur
  résiduelle), si la vérité terrain est consolidée.
