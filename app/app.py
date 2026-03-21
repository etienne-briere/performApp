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
from ui.screens.record_screen import RecordScreen
from ui.screens.view_screen import ViewScreen
from ui.screens.history_screen import HistoryScreen

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
        self.view = None
        self.record = None
        self.history = None
        self.profile = None
        self.sync = None

        logger.info("Initialisation de l'application KCApp")

    def build(self):
        '''
        Construction de l'UI
        '''
        logger.info("Construction de l'interface...")

        # Initialiser les gestionnaires
        # self.record = RecordScreen()
        # self.view = ViewScreen()
        # self.history = HistoryScreen()
        self.profile = ProfileController()
        # self.sync = SyncService()

        # Définir le thème de l'application
        self.theme_cls.theme_style = THEME_STYLE
        self.theme_cls.primary_palette = PRIMARY_PALETTE
        self.theme_cls.accent_palette = ACCENT_PALETTE

        # Charger les fichiers .kv
        Builder.load_file("ui/kv/view_screen.kv")
        Builder.load_file("ui/kv/history_screen.kv")
        Builder.load_file("ui/kv/login_dialog.kv")
        Builder.load_file("ui/kv/settings_screen.kv")
        Builder.load_file("ui/kv/record_screen.kv")
        Builder.load_file("ui/kv/home_screen.kv")
        Builder.load_file("ui/kv/main.kv")

        return Builder.load_file("ui/kv/main.kv")

    def on_start(self):
        '''
        Exécuter après le chargement de l'ui
        '''
        logger.info("Démarrage de l'application")

        # ScreenManager
        self.sm = self.root.ids.screen_manager

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