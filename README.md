# rain-gamma-spikes-france

Event-study of gamma-dose spikes after rainfall in France (RNM/ASNR × Météo-France SYNOP).

## Lancer le tableau de bord

1. Assurez-vous d'avoir installé les dépendances listées dans `requirements.txt` (par exemple avec `pip install -r requirements.txt`).
2. Exécutez la commande :
   ```bash
   python main.py
   ```
3. Le programme crée l'application Dash, configure un serveur Flask intégré et affiche dans la console des messages comme :
   ```text
   [INFO] Starting Dash server on http://127.0.0.1:8050
   Dash is running on http://127.0.0.1:8050/
   * Serving Flask app 'src.app'
   * Running on http://127.0.0.1:8050
   ```
   Ces lignes signifient que le serveur de développement de Dash/Flask tourne correctement en local sur votre machine. Le double message « Dash is running on… » provient d'abord de notre journalisation (`logging`), puis de Dash lui-même.
4. Ouvrez un navigateur web et rendez-vous à l'adresse indiquée (`http://127.0.0.1:8050`) pour visualiser le tableau de bord interactif.
5. Lorsque vous avez terminé, revenez au terminal et appuyez sur `CTRL+C` pour arrêter le serveur.

> ⚠️ Le serveur lancé de cette manière est destiné au développement. Pour un déploiement en production, il faut utiliser un serveur WSGI adapté (Gunicorn, uWSGI, etc.).

## Pipeline de données

Le script `main.py` propose aussi deux commandes supplémentaires :

- `python main.py download` : télécharge les jeux de données nécessaires dans `data/raw`.
- `python main.py clean` : déclenche le nettoyage des données et enregistre les résultats dans `data/cleaned`.

Ces commandes affichent des messages `[INFO]` semblables pour indiquer la progression des opérations.

Test SSH ok 10/22/2025 10:41:30
