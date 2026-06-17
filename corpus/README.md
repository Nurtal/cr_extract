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

Rappel : `False` = négation explicite (« pas d'alcool ») ≠ `NA` = sujet non
abordé. `cocaine` et `heroine` n'utilisent pas `NA` (absence = `False`).

## Tags expérimentaux (sans extracteur — travail futur)

Certains comptes rendus synthétiques (`cr_syn_*.json`) portent des tags qui
n'ont **pas encore d'extracteur**. Ils sont conservés et chargés normalement,
mais ignorés par l'évaluation tant qu'aucun extracteur ne les cible. Ils servent
d'amorce pour de prochaines itérations :

| Tag | Valeurs proposées | Exemple |
|-----|-------------------|---------|
| `mdma` | `True` / `False` / `NA` | `cr_syn_002` |
| `lsd` | `True` / `False` / `NA` | `cr_syn_004` |
| `amphetamines` | `True` / `False` / `NA` | `cr_syn_004` |
| `grossesse` | `True` / `False` / `NA` | `cr_syn_003` |
| `traitement_substitution` | `methadone` / `buprenorphine` / `NA` | `cr_syn_003` |

> `benzodiazepines`/`benzodiazepine_type` (cr_syn_001, cr_syn_005) et
> `hypnotiques`/`hypnotique_type` (cr_syn_001, cr_syn_006, cr_syn_007) étaient
> expérimentaux ; ils disposent désormais d'un extracteur.

Pour rendre l'un de ces tags « actif » : l'ajouter au catalogue
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
