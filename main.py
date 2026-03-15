import asyncio
import logging

from kivy.logger import Logger
from app.app import PerformApp
from utils.logger import setup_logger

async def main(app):
    """Point d'entrée asynchrone de l'application"""
    await app.async_run("asyncio")

if __name__ == '__main__':
    # Configuration du logging
    setup_logger()
    Logger.setLevel(logging.DEBUG)

    # Lancement de l'application
    app = PerformApp()
    asyncio.run(main(app))

# from kivymd.app import MDApp
# # from kivymd.tools.hotreload.app import MDApp
#
# from app.logic.profile_logic import ProfileController
# from app.core.sync_service import SyncService
# from app.widgets.folder_animation import FolderAnimation
#
# from app.screens.view_screen import ViewScreen
# from app.screens.record_screen import RecordScreen
# from app.screens.history_screen import HistoryScreen
#
# from kivy.lang import Builder
# from kivy.core.window import Window
# from kivy.metrics import dp, sp
#
# from datetime import datetime, timedelta, time
#
#
# class MyApp(MDApp):
#
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#
#         # # Thème
#         # self.theme_cls.theme_style = "Dark"
#         # self.theme_cls.primary_palette = "Blue"
#
#         # Adaptation écran
#         if Window.width < dp(500):  # pour smartphone
#             self.font_size_button = sp(15)  # taille texte boutons
#             self.font_size_button2 = sp(10)
#             self.font_style_subtitle1 = "Subtitle1"  # style du texte des sous-titres
#             self.font_style_subtitle2 = "Caption"  # style du texte des titres des encadrés
#             self.icon_size = sp(20)
#             self.smiley_icon_size = sp(40)
#         else:
#             self.font_size_button = sp(20)
#             self.font_size_button2 = sp(15)
#             self.font_style_subtitle1 = "H6"
#             self.font_style_subtitle2 = "Body2"
#             self.icon_size = sp(25)
#             self.smiley_icon_size = sp(60)
#
#         # Données smileys
#         self.smiley_data = [
#             ("emoticon-dead-outline", (1, 0, 0, 1)),  # Rouge
#             ("emoticon-sad-outline", (1, 0.4, 0, 1)),  # Orange foncé
#             ("emoticon-neutral-outline", (1, 0.7, 0, 1)),  # Jaune/orangé
#             ("emoticon-happy-outline", (0.4, 0.8, 0, 1)),  # Vert clair
#             ("emoticon-excited-outline", (0, 0.7, 0.2, 1)),  # Vert foncé
#             ("close-outline", "gray")  # Etat inconnu
#         ]
#
#         # Date du jour
#         self.today = datetime.today()
#         self.today_str = datetime.today().strftime("%d/%m/%Y")
#
#         # Instances vers les autres class Python
#         self.profile = ProfileController(app=self)
#
#         self.sync = SyncService(self)
#
#     def build(self):
#
#         # # Charger les fichiers .kv
#         # Builder.load_file("ui/login_dialog.kv")
#         # Builder.load_file("ui/view_screen.kv")
#         # Builder.load_file("ui/record_screen.kv")
#         # Builder.load_file("ui/history_screen.kv")
#
#         return Builder.load_file("ui/main.kv")
#
#     def on_start(self):
#         """Exécuter après le chargement de l'ui."""
#
#         # ScreenManager
#         self.sm = self.root.ids.screen_manager
#
#         # Vraies instances créées par le chargement des fichiers .kv
#         self.view = self.root.ids.screen_manager.get_screen("view")
#         self.view.app = self
#         self.record = self.root.ids.screen_manager.get_screen("record")
#         self.record.app = self
#         self.history = self.root.ids.screen_manager.get_screen("history")
#         self.history.app = self
#
#
# if __name__ == "__main__":
#     MyApp().run()

