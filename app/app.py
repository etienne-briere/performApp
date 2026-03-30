# Class KivyMD
from kivymd.app import MDApp

# Class Kivy
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import StringProperty, ListProperty

from datetime import datetime, timedelta, time


# Custom modules
from app.data.csv_storage import CsvStorage
from config import THEME_STYLE, PRIMARY_PALETTE, ACCENT_PALETTE
# from app.logic.profile_logic import ProfileController
from app.data.training_data_repository import TrainingDataRepository
from app.data.file_importer import FileImporter
from ui.widgets.exercise_dropdown import ExerciseDropdown 

# Logger
from utils.logger import get_logger

logger = get_logger(__name__)


class PerformApp(MDApp):
    """
    Application principale PerformApp
    """
    
    selected_exercise = StringProperty("")
    exercise_history = ListProperty([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialisation des attributs de l'application
        self.repo = None
        self.importer = None
        self.storage = None

        logger.info("Initialisation de l'application")

    def build(self):
        '''
        Construction de l'UI
        '''
        logger.info("Construction de l'interface...")

        # Initialiser les gestionnaires
        self.repo = TrainingDataRepository()
        self.importer = FileImporter(repo=self.repo)
        self.storage = CsvStorage(folder_path="my_training_data")

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
        Builder.load_file("ui/kv/topbar.kv")
        Builder.load_file("ui/kv/exercise_dropdown.kv")

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
    
    def on_selected_exercise(self, instance, value):
        """Réagit au changement de l'exercice sélectionné"""
        if not value:
            return

        print(f"Exercice sélectionné : {value}")

        # 🔥 récupérer le repo
        repo = self.repo

        # 🔥 mettre à jour l’historique automatiquement
        self.exercise_history = repo.get_exercise_history(value, repo.database)

        print(f"Historique mis à jour : {self.exercise_history}")