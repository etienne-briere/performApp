import os

# Configuration de l'application
APP_TITLE = 'PerformApp'
DEBUG_MODE = os.getenv('DEBUG', 'True').lower() == 'true'

# Configuration du thème
THEME_STYLE = "Dark"  # "Light" ou "Dark"
PRIMARY_PALETTE = "Blue"
ACCENT_PALETTE = "Amber"

# PARAMETRES
SERIE_COUNT = 4  # Nombre de séries à afficher par défaut dans l'écran d'enregistrement
ROW_HISTORY_COUNT = 5  # Nombre de lignes à afficher dans l'historique (pagination)




