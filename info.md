# SEMERAP Eau

Intégration Home Assistant communautaire et non officielle pour récupérer les relevés de consommation d'eau du portail client SEMERAP.

## Fonctionnalités

- Connexion au portail client SEMERAP depuis le flux de configuration Home Assistant.
- Récupération automatique des relevés disponibles et actualisation quotidienne.
- Archivage local persistant des relevés, sans suppression des données historiques conservées localement.
- Six entités de suivi, dont l'index du compteur, la consommation du dernier relevé et les dates.
- Import manuel de relevés historiques avec le service `semerap.import_readings`.

## Installation

Installer **SEMERAP Eau** depuis HACS, puis redémarrer Home Assistant. Ajouter ensuite l'intégration depuis **Paramètres → Appareils et services → Ajouter une intégration** et renseigner les identifiants du portail SEMERAP.

Le dépôt peut également être ajouté dans HACS comme dépôt personnalisé de type **Intégration**.

## Limites

- L'API du portail n'est pas officiellement documentée et peut évoluer.
- La fréquence et la disponibilité des relevés dépendent de SEMERAP ; les compteurs ne sont pas nécessairement relevés quotidiennement.
- Plusieurs points de comptage sur un même compte : seul le premier est actuellement sélectionné.
- Les relevés historiques archivés sont exposés dans les attributs du capteur et dans le stockage local, mais ne sont pas réinjectés dans l'historique Recorder de Home Assistant.

Cette intégration est indépendante de SEMERAP et n'est ni affiliée, ni supportée, ni approuvée par SEMERAP. Le logo et les marques SEMERAP restent la propriété de leurs détenteurs.
