# Corpus annoté — comptes rendus en JSON

Un fichier JSON par compte rendu (`cr_000.json`, `cr_001.json`, …). C'est le
**corpus d'évaluation éditable** : on peut y ajouter des comptes rendus
synthétiques, ajuster les tags d'un CR, ou introduire de nouveaux tags pour un
travail ultérieur.

Généré à partir de `comptes_rendus_medicaux.csv` ; les deux sources donnent un
résultat d'évaluation identique. **Toutes les données sont fictives.**

## Schéma d'un fichier

```json
{
  "id": "cr_000",
  "texte": "COMPTE RENDU ...",
  "tags": {
    "situation_professionnelle": "inactif",
    "alcool": "True"
  }
}
```

- `id` : identifiant du compte rendu (libre, sert au repérage).
- `texte` : le compte rendu brut (texte libre).
- `tags` : annotations de référence (gold), `clé_de_tag: valeur` — les valeurs
  sont les **chaînes canoniques** comparées directement aux prédictions.

## Tags reconnus et valeurs autorisées

| Tag | Champ | Valeurs |
|-----|-------|---------|
| `situation_conjugale` | Célibataire / en couple | `en couple` / `célibataire` / `NA` |
| `situation_professionnelle` | Situation professionnelle | `actif` / `inactif` / `NA` |
| `sdf` | SDF / absence de logement | `True` / `False` / `NA` |
| `protection_juridique` | Curatelle / Tutelle | `curatelle` / `tutelle` / `NA` |
| `sevrages_compliques` | Antécédents de sevrages compliqués | `True` / `False` / `NA` |
| `alcool` | Consommation actuelle d'alcool | `True` / `False` / `NA` |
| `tabac` | Consommation actuelle de tabac | `True` / `False` / `NA` |
| `cannabis` | Cannabis / THC / CBD | `Cannabis` / `THC` / `CBD` / `NA` |
| `cocaine` | Cocaïne | `True` / `False` |
| `cocaine_voie` | Cocaïne - voie d'administration | `nasale` / `intraveineuse` / `NA` |
| `heroine` | Héroïne | `True` / `False` |
| `heroine_quantite` | Héroïne - quantité | nombre en chaîne (ex. `"0.5"`) / `NA` |
| `ketamine` | Kétamine | `True` / `False` / `NA` |
| `benzodiazepines` | Benzodiazépines | `True` / `False` / `NA` |
| `benzodiazepine_type` | Benzodiazépine - type | DCI (`zolpidem`, `alprazolam`…) / `NA` |
| `hypnotiques` | Hypnotiques | `True` / `False` / `NA` |
| `hypnotique_type` | Hypnotique - type | DCI (`zopiclone`, `zolpidem`…) / `NA` |
| `mdma` | MDMA | `True` / `False` / `NA` |
| `lsd` | LSD | `True` / `False` / `NA` |
| `amphetamines` | Amphétamines | `True` / `False` / `NA` |
| `grossesse` | Grossesse | `True` / `False` / `NA` |
| `hepatopathie` | Hépatopathie | `True` / `False` / `NA` |
| `suivi_hepato_gastro` | Suivi hépato-gastro-entérologie | `True` / `False` / `NA` |
| `pancreatite` | Pancréatite | `True` / `False` / `NA` |
| `cardiovasculaire` | Problèmes cardiovasculaires | `True` / `False` / `NA` |
| `bpco` | BPCO | `True` / `False` / `NA` |
| `emphyseme` | Emphysème | `True` / `False` / `NA` |
| `diabete` | Diabète | `True` / `False` / `NA` |
| `troubles_cognitifs` | Troubles cognitifs | `True` / `False` / `NA` |
| `depression` | Épisode dépressif / dépression | `True` / `False` / `NA` |
| `troubles_anxieux` | Troubles anxieux | `True` / `False` / `NA` |
| `troubles_bipolaires` | Troubles bipolaires | `True` / `False` / `NA` |
| `tentative_suicide` | Tentative de suicide | `True` / `False` / `NA` |
| `psychotropes` | Utilisation de psychotropes | `True` / `False` / `NA` |
| `addictolytique` | Addictolytique | `True` / `False` / `NA` |
| `addictolytique_type` | Addictolytique - type | DCI (`acamprosate`, `methadone`…) / `NA` |
| `traitement_substitution` | Traitement de substitution | `True` / `False` / `NA` |
| `traitement_substitution_type` | Traitement de substitution - type | `methadone` / `buprenorphine` / `NA` |

Rappel : `False` = négation explicite (« pas d'alcool ») ≠ `NA` = sujet non
abordé. `cocaine` et `heroine` n'utilisent pas `NA` (absence = `False`).

## Tags expérimentaux (sans extracteur — travail futur)

Un tag *expérimental* est un tag annoté dans le corpus mais sans extracteur : il
est conservé et chargé normalement, simplement ignoré par l'évaluation tant
qu'aucun extracteur ne le cible. C'est l'amorce d'une prochaine itération.

> **Aucun pour l'instant** : tous les tags annotés du corpus disposent désormais
> d'un extracteur (couverture complète). Pour en introduire un nouveau, l'annoter
> dans un ou plusieurs `cr_syn_*.json` puis suivre la procédure ci-dessous.

Pour rendre un tag « actif » : l'ajouter au catalogue
(`cr_extract/modele.py`) puis écrire l'extracteur correspondant dans
`cr_extract/extracteurs/` — l'évaluation le prendra alors en compte
automatiquement.

## Ajouter / modifier des données

- **Nouveau compte rendu** : déposer un fichier `cr_xxx.json` (n'importe quel
  nom unique) respectant le schéma. Il est automatiquement pris en compte.
- **Annoter plus ou moins de tags** : ne mettre dans `tags` que ceux qui sont
  pertinents ; un tag absent est **ignoré** à l'évaluation (annotation
  partielle, distincte d'une annotation `NA`).
- **Nouveau tag** (travail futur) : ajouter une clé inédite ; elle est conservée
  et chargée, prête à être ciblée par un futur extracteur.

## Utilisation

```python
from cr_extract.corpus import charger_corpus, csv_vers_corpus
from cr_extract.evaluation import evaluer_corpus, rapport_markdown

# (Re)générer le corpus depuis le CSV
csv_vers_corpus("comptes_rendus_medicaux.csv", "corpus")

# Charger et évaluer le corpus
crs = charger_corpus("corpus")
print(rapport_markdown(evaluer_corpus("corpus")))
```

En ligne de commande :

```bash
python -m cr_extract.cli corpus comptes_rendus_medicaux.csv -o corpus   # (re)générer
python -m cr_extract.cli evaluer corpus                                  # évaluer le dossier
```
