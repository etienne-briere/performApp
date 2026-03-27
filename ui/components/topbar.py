from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.menu import MDDropdownMenu

from kivy.properties import StringProperty
from kivy.app import App
from kivy.metrics import dp, sp

class TopBar(MDTopAppBar):
    title = StringProperty("Accueil")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialisation des variables
        self.profile_menu = None

        app=App.get_running_app()
        self.importer = app.importer # Accès à l'importateur de fichiers via l'application
        self.repo = app.repo # Accès à la base de données via l'application

    def on_profile_press(self, *args):
        self.open_profile_menu(args[0])

    def open_profile_menu(self, button):
        """
        Ouvre un menu déroulant
        :param button: bouton cliqué
        :return:
        """
        if not self.profile_menu:
            menu_items = [
                {
                    "text": "Importer ton fichier",
                    "trailing_icon": "download",
                    "on_release": lambda: (
                        self.importer.open(),
                        self.profile_menu.dismiss()
                    )
                },
                {
                    "text": "Exporter ton fichier",
                    "trailing_icon": "file-plus",
                    "on_release": lambda: (
                        print("Exporter cliqué"), 
                        self.profile_menu.dismiss()
                    )
                },
            ]

            self.profile_menu = MDDropdownMenu(
                caller=button,
                items=menu_items,
                width_mult=4,
                radius=dp(10),
            )

        self.profile_menu.open()

    def on_settings_press(self, *args):
        print("Settings cliqué")

    