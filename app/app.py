# Class KivyMD
from kivymd.app import MDApp

# Class Kivy
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.metrics import dp, sp

from datetime import datetime, timedelta, time


# Custom modules
from config import THEME_STYLE, PRIMARY_PALETTE, ACCENT_PALETTE
from app.logic.profile_logic import ProfileController
from app.core.sync_service import SyncService
from app.widgets.folder_animation import FolderAnimation

# Logger
from utils.logger import get_logger

logger = get_logger(__name__)


class PerformApp(MDApp):
    """
    Application principale PerformApp
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialisation des attributs de l'application
        self.profile = None
        self.sync = None

        logger.info("Initialisation de l'application KCApp")

    def build(self):
        '''
        Construction de l'UI
        '''
        logger.info("Construction de l'interface...")

        # Initialiser les gestionnaires
        self.profile = ProfileController(app=self)
        self.sync = SyncService(self)

        # Définir le thème de l'application
        self.theme_cls.theme_style = THEME_STYLE
        self.theme_cls.primary_palette = PRIMARY_PALETTE
        self.theme_cls.accent_palette = ACCENT_PALETTE

        # Adaptation écran
        if Window.width < dp(500):  # pour smartphone
            self.font_size_button = sp(15)  # taille texte boutons
            self.font_size_button2 = sp(10)
            self.font_style_subtitle1 = "Subtitle1"  # style du texte des sous-titres
            self.font_style_subtitle2 = "Caption"  # style du texte des titres des encadrés
            self.icon_size = sp(20)
            self.smiley_icon_size = sp(40)
        else:
            self.font_size_button = sp(20)
            self.font_size_button2 = sp(15)
            self.font_style_subtitle1 = "H6"
            self.font_style_subtitle2 = "Body2"
            self.icon_size = sp(25)
            self.smiley_icon_size = sp(60)

        # Charger les fichiers .kv
        Builder.load_file("ui/kv/view_screen.kv")
        Builder.load_file("ui/kv/history_screen.kv")
        Builder.load_file("ui/kv/login_dialog.kv")
        Builder.load_file("ui/kv/settings_screen.kv")
        Builder.load_file("ui/kv/record_screen.kv")
        Builder.load_file("ui/kv/home_screen.kv")
        Builder.load_file("ui/kv/main.kv")

        # Données smileys
        self.smiley_data = [
            ("emoticon-dead-outline", (1, 0, 0, 1)),  # Rouge
            ("emoticon-sad-outline", (1, 0.4, 0, 1)),  # Orange foncé
            ("emoticon-neutral-outline", (1, 0.7, 0, 1)),  # Jaune/orangé
            ("emoticon-happy-outline", (0.4, 0.8, 0, 1)),  # Vert clair
            ("emoticon-excited-outline", (0, 0.7, 0.2, 1)),  # Vert foncé
            ("close-outline", "gray")  # Etat inconnu
        ]

        # Date du jour
        self.today = datetime.today()
        self.today_str = datetime.today().strftime("%d/%m/%Y")

        return Builder.load_file("ui/main.kv")

    def on_start(self):
        '''
        Exécuter après le chargement de l'ui
        '''
        logger.info("Démarrage de l'application")

        # ScreenManager
        self.sm = self.root.ids.screen_manager

        # # Vraies instances créées par le chargement des fichiers .kv
        # self.view = self.root.ids.screen_manager.get_screen("view")
        # self.view.app = self
        # self.record = self.root.ids.screen_manager.get_screen("record")
        # self.record.app = self
        # self.history = self.root.ids.screen_manager.get_screen("history")
        # self.history.app = self

    def on_stop(self):
        """
        Appelé à l'arrêt de l'application
        """

        logger.info("Arrêt de l'application")


    def change_screen(self, screen_name, title):
        """Change l'écran actif et met à jour le titre de la top bar

        Args:
            screen_name: Nom de l'écran à afficher
            title: Nouveau titre pour la top bar
        """
        self.root.ids.screen_manager.current = screen_name
        self.root.ids.top_bar.title = title