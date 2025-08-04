![logo](../../plugin_info/refoss_icon.png | width=100)
# Plugin Refoss EM - Beta

## Description

Grâce à ce plugin, vous récupérez par le réseau local les données de vos moniteurs d'énergie Refoss.

Il récupère la tension, le courant, la puissance, le facteur de puissance et la consommation totale de chaque canal.

Pas de connexion au cloud Refoss n'est requise.

Ce plugin permet la détection automatique sur le réseau local.

## Pré-Requis
- Connectez vos moniteurs d'énergie Refoss à votre réseau
- Affectez leur une adresse IP fixe pour éviter de devoir reconfigurer l'équipement en cas de changement d'adresse IP.

## Installation

- Télécharger le plugin depuis le market
- Activer le plugin
- L’installation des dépendances devrait débuter sauf si la gestion automatique a été désactivée au préalable.

## Configuration

- **Cycle d'actualisation** : Fréquence de récupération des données de tension, puissance, ...
- **Port du socket interne** : Ne modifiez cette valeur que si vous avez un conflit avec un autre plugin.

## Equipements

Les équipements sont accessibles à partir du menu Plugins → Energie → Refoss EM.

### Découverte des équipements

Depuis la page de configuration des équipements, cliquer sur le bouton Découverte.

Vous pouvez éventuellement renseigner l’adresse IP du moniteur d'énergie. Cette étape est nécessaire s'il ne se trouve pas sur le même sous-réseau que Jeedom.

![Decouverte](../images/decouverte.png)

Cette étape peut prendre jusqu'à 30 secondes. Un message vous informeras du résultat de la découverte.

![DecouverteOK](../images/decouverteok.png)
![DecouverteKO](../images/decouverteko.png)

### Les commandes

Pour chaque équipements, vous avez les commandes informations suivantes pour chaque canal :
- Tension en Volt
- Courant en Ampère
- Puissance en Watt
- Facteur de puissance
- Consommation totale en kWh