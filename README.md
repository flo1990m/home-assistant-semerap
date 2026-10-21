# SEMERAP Eau pour Home Assistant

Intégration **non officielle** pour consulter les relevés d’eau du portail SEMERAP dans Home Assistant.

![SEMERAP](custom_components/semerap/brand/logo.png)

## Installation via HACS

1. Dans HACS, ouvrez **Intégrations**, menu **⋮**, **Dépôts personnalisés**.
2. Ajoutez `https://github.com/flo1990m/home-assistant-semerap` comme type **Intégration**.
3. Installez **SEMERAP Eau**, redémarrez Home Assistant Core.
4. **Paramètres → Appareils et services → Ajouter une intégration → SEMERAP Eau** : indiquez votre identifiant et votre mot de passe du portail.

Pour migrer depuis les versions 0.1/0.2 installées manuellement : ne supprimez ni l’intégration ni les appareils. Laissez HACS remplacer le dossier `custom_components/semerap`, puis redémarrez Core. Les identifiants uniques des six entités restent inchangés. Sauvegardez HA auparavant.

## Fonctionnalités

- Authentification via le portail SEMERAP (API non officielle), reconnexion automatique à expiration du jeton.
- Découverte des points de comptage (le premier est sélectionné si plusieurs existent).
- Actualisation automatique **une fois toutes les 24 heures**.
- Stockage persistant de tous les relevés reçus dans `.storage/semerap.<point>.readings` (fusion par date et préservation des relevés retirés du site).
- Six entités : index du compteur (m³), consommation du dernier relevé (m³), moyenne quotidienne (m³/j), date du dernier relevé, date au format français, moyenne historique fournie par SEMERAP.
- Dans les attributs du capteur **Index compteur** : `readings_count` et `readings` avec dates ISO et françaises.
- Logo et icône locaux compatibles avec Home Assistant 2026.3 et versions ultérieures.

## Limites importantes

- Les relevés ne sont disponibles qu’à la fréquence à laquelle SEMERAP relève le compteur (souvent semestrielle).
- Les anciennes dates sont archivées dans les attributs et le stockage local, **pas injectées dans l’historique Recorder**.
- Dans le tableau de bord Énergie, une consommation sur plusieurs mois apparaîtra au moment du nouvel index, **pas comme mesure quotidienne**.
- L’API n’est pas documentée officiellement et peut changer.
- Plusieurs points de comptage : seule la première référence est actuellement configurée.
- Les identifiants sont dans les données privées de configuration Home Assistant ; ne publiez jamais `.storage`.
- Le logo appartient à SEMERAP. Ce projet n’est pas affilié à SEMERAP.

## Version 1.0.0

Première publication GitHub/HACS, archive locale persistante, six capteurs et image de marque.


## Import de relevés historiques (v1.1.0)

Dans Home Assistant, ouvrir **Outils de développement > Actions**, puis choisir
`semerap.import_readings`. Les relevés sont sauvegardés dans l'archive persistante
de l'intégration et immédiatement rendus disponibles dans l'attribut `readings`
du capteur d'index.

Exemple en YAML :

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

- `date` : format `YYYY-MM-DD`, obligatoire ;
- `index` : index numérique non négatif en m³, obligatoire ;
- `consumption` : volume consommé depuis le relevé précédent, facultatif ;
- `type`, `counterRef` : métadonnées facultatives ;
- `pdc_ref` : facultatif si une seule configuration SEMERAP existe.

Les dates déjà présentes sont conservées (l'import ne les remplace pas).
Les valeurs de l'API SEMERAP continueront à être mises à jour lors de la synchronisation quotidienne.

**Attention :** en cas de remplacement du compteur, ne jamais soustraire directement
l'index de l'ancien compteur de celui du nouveau. Renseigner la consommation
facturée sur chaque relevé pour une comparaison historique correcte.

