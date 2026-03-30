from kivymd.uix.button import MDRectangleFlatIconButton
from kivymd.uix.menu import MDDropdownMenu
from kivy.app import App
from kivy.properties import StringProperty
from config import FONT_SIZE_BUTTON
from kivy.properties import NumericProperty

class ExerciseDropdown(MDRectangleFlatIconButton):

    # Properties pour l'UI
    font_size_button = NumericProperty(FONT_SIZE_BUTTON) # taille du texte des boutons

    def on_release(self):
        app = App.get_running_app()
        items = app.repo.exercise_names

        if not items:
            return

        menu_items = [
            {
                "text": name,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=name: self.select_exercise(x),
            }
            for name in items
        ]

        self.menu = MDDropdownMenu(
            caller=self,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()
    
    def select_exercise(self, name):
        app = App.get_running_app()
        app.selected_exercise = name # déclenche la mise à jour de l'historique via on_selected_exercise dans app.py

        # Fermer le menu
        if hasattr(self, "menu"):
            self.menu.dismiss()