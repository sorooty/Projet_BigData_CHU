# Connexion PowerBI - CHU Gold

## Prérequis

- PowerBI Desktop installé
- Connecteur PostgreSQL : télécharger depuis https://www.npgsql.org/doc/installation.html
- Pipeline Airflow executé au moins une fois (tables Gold alimentées)

## Connexion aux vues Gold

1. Ouvrir PowerBI Desktop
2. **Accueil** > **Obtenir des données** > **Base de données** > **Base de données PostgreSQL**
3. Renseigner :
   - Serveur : `localhost` (ou IP du serveur en prod)
   - Base de données : `chu_data`
4. Mode de connectivité : **Importer** (recommandé)
5. Dans le navigateur, sélectionner les 4 vues :
   - `gold.v_kpi_consultations`
   - `gold.v_kpi_deces`
   - `gold.v_kpi_satisfaction`
   - `gold.v_kpi_hospitalisations` (vide jusqu alimentation fait_hospitalisation)

## Rafraichissement

Le pipeline tourne a minuit (`0 0 * * *`). Configurer le rafraichissement PowerBI apres :
- **Gérer les actualisations planifiées** > chaque jour a 01h00

## Modele de données recommande

Dans PowerBI, relier les vues sur les clés communes :

```
v_kpi_consultations.annee       --> v_kpi_deces.annee
v_kpi_consultations.finess      --> v_kpi_satisfaction.finess
v_kpi_consultations.libelle_region --> v_kpi_deces.libelle_region
```

## Indicateurs métier a construire

| Mesure DAX | Description |
|---|---|
| `Nb consultations` | `SUM(v_kpi_consultations[nb_consultations])` |
| `Durée moy. consultation` | `AVERAGE(v_kpi_consultations[duree_moy_min])` |
| `Nb décès` | `SUM(v_kpi_deces[nb_deces])` |
| `Score satisfaction moyen` | `AVERAGE(v_kpi_satisfaction[score_moyen])` |
| `Taux satisfaction >80` | `CALCULATE(COUNTROWS(...), [score_moyen] > 80)` |

## DirectQuery (optionnel)

Utiliser DirectQuery uniquement si les données doivent etre en temps reel.
Attention : les vues aggregees supportent mal le DirectQuery sur gros volumes.
