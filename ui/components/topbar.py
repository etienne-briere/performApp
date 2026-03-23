from kivymd.uix.toolbar import MDTopAppBar
from kivy.properties import StringProperty
from kivy.app import App

class TopBar(MDTopAppBar):
    title = StringProperty("Accueil")

    # def init(self):
    #     """
    #     Exécuter juste avant que l'écran devienne visible.
    #     """
        
    #     app = App.get_running_app()

    #     # Managers
    #     self.profile = app.profile
    #     self.view = app.view

    def on_profile_press(self, *args):
        print("Profil cliqué")
        app = App.get_running_app()

        # Managers
        self.profile = app.profile
        self.profile.on_profile_icon_press()

    def on_settings_press(self, *args):
        print("Settings cliqué")