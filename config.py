import os
from kivy.core.window import Window
from kivy.metrics import dp, sp

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

# Données smileys
# SMILEY_DATA = [
#     ("emoticon-dead-outline", (1, 0, 0, 1)),  # Rouge
#     ("emoticon-sad-outline", (1, 0.4, 0, 1)),  # Orange foncé
#     ("emoticon-neutral-outline", (1, 0.7, 0, 1)),  # Jaune/orangé
#     ("emoticon-happy-outline", (0.4, 0.8, 0, 1)),  # Vert clair
#     ("emoticon-excited-outline", (0, 0.7, 0.2, 1)),  # Vert foncé
#     ("close-outline", "gray")  # Etat inconnu
# ]
SMILEY_DATA = [
    {
        "rpe": 1,
        "icon": "emoticon-dead-outline",
        "color": (1, 0, 0, 1)
    },
    {
        "rpe": 2,
        "icon": "emoticon-sad-outline",
        "color": (1, 0.4, 0, 1)
    },
    {
        "rpe": 3,
        "icon": "emoticon-neutral-outline",
        "color": (1, 0.7, 0, 1)
    },
    {
        "rpe": 4,
        "icon": "emoticon-happy-outline",
        "color": (0.4, 0.8, 0, 1)
    },
    {
        "rpe": 5,
        "icon": "emoticon-excited-outline",
        "color": (0, 0.7, 0.2, 1)
    }
]

# Adaptation écran
if Window.width < dp(500):  # pour smartphone
    FONT_SIZE_BUTTON = sp(15)  # taille texte boutons
    FONT_SIZE_BUTTON2 = sp(10)
    FONT_STYLE_SUBTITLE1 = "Subtitle1"  # style du texte des sous-titres
    FONT_STYLE_SUBTITLE2 = "Caption"  # style du texte des titres des encadrés
    ICON_SIZE = sp(20)
    SMILEY_ICON_SIZE = sp(40)
else:
    FONT_SIZE_BUTTON = sp(20)
    FONT_SIZE_BUTTON2 = sp(15)
    FONT_STYLE_SUBTITLE1 = "H6"
    FONT_STYLE_SUBTITLE2 = "Body2"
    ICON_SIZE = sp(25)
    SMILEY_ICON_SIZE = sp(60)




