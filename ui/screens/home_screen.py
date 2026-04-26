from kivymd.uix.screen import MDScreen

class HomeScreen(MDScreen):
    def on_enter(self):
        self.ids.title_label.text = "Bienvenue !"

    def on_settings_press(self, *args):
        self.parent.current = "settings"
