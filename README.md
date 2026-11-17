# SEMERAP Eau pour Home Assistant

Intégration Home Assistant permettant de consulter automatiquement les relevés de votre compteur d’eau SEMERAP et de conserver leur historique localement.

![SEMERAP Eau](custom_components/semerap/brand/logo.png)

[![HACS](https://img.shields.io/badge/HACS-Intégration-blue.svg)](https://www.hacs.xyz/)
[![Version](https://img.shields.io/badge/version-1.1.5-informational.svg)](https://github.com/flo1990m/home-assistant-semerap/releases)
[![Licence](https://img.shields.io/github/license/flo1990m/home-assistant-semerap)](LICENSE)

## Installation

SEMERAP Eau est disponible dans le **catalogue officiel HACS**. Aucun dépôt personnalisé n’est nécessaire.

1. Ouvrez **HACS** dans Home Assistant.
2. Allez dans **Intégrations**, puis recherchez **SEMERAP Eau**.
3. Ouvrez la fiche de l’intégration et sélectionnez **Télécharger**.
4. Redémarrez Home Assistant.
5. Allez dans **Paramètres → Appareils et services → Ajouter une intégration**.
6. Recherchez **SEMERAP Eau**, puis renseignez les identifiants de votre espace client SEMERAP.

Les mises à jour suivantes seront proposées directement par HACS.

## Fonctionnalités

- Connexion à votre espace client SEMERAP avec votre identifiant et votre mot de passe.
- Renouvellement de session et procédure de réauthentification lorsque les identifiants ou le jeton ne sont plus valides.
- Détection des points de comptage disponibles (le premier point est sélectionné lorsqu’il y en a plusieurs).
- Actualisation automatique des données toutes les 24 heures.
- Conservation persistante des relevés reçus, même lorsqu’ils ne sont plus présents sur le portail.
- Fusion des relevés par date afin d’éviter les doublons.
- Import manuel de relevés historiques avec l’action Home Assistant `semerap.import_readings`.

### Entités disponibles

L’intégration crée six entités :

- **Index du compteur** : dernier index connu, en m³.
- **Consommation du dernier relevé** : volume consommé depuis le relevé précédent, en m³.
- **Moyenne quotidienne** : consommation moyenne quotidienne, en m³/j.
- **Date du dernier relevé** : date du dernier relevé reçu.
- **Date du dernier relevé (format français)** : date présentée au format français.
- **Moyenne historique SEMERAP** : moyenne communiquée par le service SEMERAP.

Le capteur **Index du compteur** expose également les attributs `readings_count` et `readings`, qui contiennent les relevés archivés avec leurs dates.

## Importer des relevés historiques

L’action `semerap.import_readings` permet d’ajouter des relevés plus anciens à l’archive locale de l’intégration.

Dans Home Assistant, ouvrez **Outils de développement → Actions**, puis choisissez `semerap.import_readings`.

Exemple :

```yaml
action: semerap.import_readings
data:
  pdc_ref: "18929"
  readings:
    - date: "2020-05-25"
      index: 488
      consumption: 20
      type: radio
      counterRef: "06Z0205521"
```

- `date` : date au format `YYYY-MM-DD`, obligatoire.
- `index` : index numérique non négatif en m³, obligatoire.
- `consumption` : consommation depuis le relevé précédent, facultative.
- `type` et `counterRef` : métadonnées facultatives.
- `pdc_ref` : référence du point de comptage ; facultative si une seule configuration SEMERAP existe.

Les dates déjà présentes dans l’archive sont conservées : l’import ne les remplace pas. Les synchronisations automatiques suivantes continuent de mettre à jour les données provenant de SEMERAP.

## À savoir

- La fréquence des relevés dépend de SEMERAP et de votre compteur ; elle peut être espacée de plusieurs mois. L’intégration interroge le portail une fois par jour, mais ne peut pas créer de nouveaux relevés si SEMERAP n’en a pas publié.
- Les relevés archivés sont conservés dans le stockage local de l’intégration et exposés dans les attributs du capteur d’index. Ils ne sont pas injectés rétroactivement dans l’historique Recorder de Home Assistant.
- Dans le tableau de bord Énergie, la consommation entre deux index est donc associée au moment où le nouvel index est reçu, et non répartie automatiquement sur chaque jour de la période.
- Si plusieurs points de comptage sont associés au compte, seul le premier est actuellement configuré.
- L’intégration utilise une API non officielle du portail SEMERAP, susceptible d’évoluer.

## Migration depuis une installation manuelle

Si vous utilisez une ancienne version 0.1 ou 0.2 installée manuellement, ne supprimez pas l’intégration ni ses appareils. Installez SEMERAP Eau depuis HACS, laissez HACS remplacer le dossier `custom_components/semerap`, puis redémarrez Home Assistant. Les identifiants uniques des six entités sont conservés. Effectuez une sauvegarde de Home Assistant avant la migration.

## Assistance et contributions

- [Signaler un problème](https://github.com/flo1990m/home-assistant-semerap/issues)
- [Consulter les versions](https://github.com/flo1990m/home-assistant-semerap/releases)
- [Code source](https://github.com/flo1990m/home-assistant-semerap)

## Licence et affiliation

Ce projet est indépendant et n’est pas affilié à SEMERAP. Le logo SEMERAP appartient à son propriétaire.
