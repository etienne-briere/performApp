from app.data.file_importer import FileImporter
from app.data.data_converter import DataConverter
from app.data.csv_storage import CsvStorage
from kivy.app import App
from kivy.properties import ListProperty
from kivy.event import EventDispatcher

class TrainingDataRepository(EventDispatcher):

    exercise_names = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs) # important pour les properties
        
        app=App.get_running_app()
        
        # Managers
        self.importer = app.importer
        # self.storage = app.storage
        
        # Initialisation de la base de données en mémoire et du stockage
        self.database = {"exercise_library": {}, "sessions": [], "body_weight_history": []}

    def load_from_file(self, raw):
        """Point d'entrée unique : importe et convertit."""

        # Convertir
        convert = DataConverter()
        self.database = convert.from_legacy(raw)
        print(f"Dictionnaire converti : {self.database}")

        # Sauvegarder
        # self.storage.export(self.database)

        # Mettre à jour l'état global
        self.exercise_names = self.get_exercise_names(self.database)
        print(self.exercise_names)

    def get_exercise_names(self, database):
        return [ex["name"] for ex in database["exercise_library"].values()]

    def get_sessions(self, database):
        return database["sessions"]
    
    def get_exercise_id(self, name, data):
        for ex_id, ex in data["exercise_library"].items():
            if ex["name"] == name:
                return ex_id
        return None
    
    def get_exercise_history(self, exercise_name, data):
        exercise_id = self.get_exercise_id(exercise_name, data)

        if exercise_id is None:
            return []

        history = []

        for session in data["sessions"]:
            date = session["date"]

            for ex in session["exercises"]:
                if ex["exercise_id"] == exercise_id:
                    history.append({
                        "date": date,
                        "sets": ex["sets"],
                        "rpe": ex["rpe"],
                        "notes": ex["notes"]
                    })

        return history

    def on_exercise_names(self, instance, value):
        """on_<property> = réaction automatique à un changement d’état de <property>"""
        if value:
            app = App.get_running_app()

            # Si aucun exercice n'est encore sélectionné, sélectionner le 1er de la liste pour déclencher l’affichage de l’historique
            if not app.selected_exercise:
                app.selected_exercise = value[0] # déclenche la mise à jour de l’historique via on_selected_exercise dans app.py