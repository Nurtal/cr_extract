"""Extracteur de la situation professionnelle (#2) — champ « difficile ».

Catégoriel : ``actif`` / ``inactif`` / ``NA``, avec **score de confiance**.

- ``inactif`` : sans emploi, retraité, invalidité, AAH, arrêt de travail, au
  foyer, chômage, cursus interrompu… (marqueurs forts, prioritaires).
- ``actif`` : en activité, activité maintenue, salarié, apte, apprentissage,
  reprise d'activité…
- ``NA`` : information non renseignée / emploi « non connu ».

Les marqueurs d'inactivité priment sur une mention résiduelle d'« activité »
(ex. « en arrêt de travail » l'emporte), car ils décrivent le statut courant.
"""

from __future__ import annotations

import re

from cr_extract.modele import CHAMPS_PAR_CLE, ResultatExtraction
from cr_extract.extracteurs import enregistrer

_INACTIF = re.compile(
    r"(?<!\w)(sans emploi|sans activite|pas d'activite|pas d'emploi|sans profession|"
    r"retraite\w*|invalidite|en invalidite|\baah\b|arret de travail|au foyer|"
    r"mere au foyer|pere au foyer|chomage|chomeur\w*|inactif|inactive|inactivite|"
    r"ehpad|interrompu son cursus|descolaris\w*)"
)

# « actif » seul est évité : il qualifie souvent une consommation (« tabac
# actif », « tabagisme actif ») et non l'emploi. On ne retient que les tournures
# professionnelles (« actuellement actif », « (actif) », « en activité »…).
_ACTIF = re.compile(
    r"(?<!\w)(en activite|activite maintenue|actuellement actif|\(actif|"
    r"salarie\w*|\bapte\b|en apprentissage|apprentissage|"
    r"reprise d'une activite|repris une activite|etudiant\w*|interim\w*|"
    r"en poste|en emploi|profession liberale|fonctionnaire)(?!\w)"
)


@enregistrer("situation_professionnelle")
class ExtracteurSituationProfessionnelle:
    champ = CHAMPS_PAR_CLE["situation_professionnelle"]

    def extraire(self, texte_normalise: str, texte_origine: str) -> ResultatExtraction:
        # On ne traite pas l'absence d'information par un marqueur global : un
        # « non renseigné » porte souvent sur un autre item (conjugal, logement),
        # tandis qu'un « sans emploi » explicite doit primer. L'absence de tout
        # marqueur professionnel se traduit naturellement par NA (cas par défaut).
        inactif = _INACTIF.search(texte_normalise)
        actif = _ACTIF.search(texte_normalise)

        if inactif and not actif:
            return ResultatExtraction("inactif", 0.9, inactif.group(0))
        if actif and not inactif:
            return ResultatExtraction("actif", 0.9, actif.group(0))
        if inactif and actif:
            # Conflit : le marqueur d'inactivité (statut courant) l'emporte avec
            # une confiance abaissée pour signaler l'ambiguïté.
            return ResultatExtraction("inactif", 0.6, inactif.group(0))
        return ResultatExtraction.absent()
