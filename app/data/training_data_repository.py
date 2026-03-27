from app.data.file_importer import FileImporter
from app.data.data_converter import DataConverter
from app.data.csv_storage import CsvStorage
from kivy.app import App


class TrainingDataRepository:

    def __init__(self):
        app=App.get_running_app()
        # Managers
        self.importer = app.importer
        self.storage = app.storage
        
        # Initialisation de la base de données en mémoire et du stockage
        # self.database = {"exercise_library": {}, "sessions": [], "body_weight_history": []}

    def load_from_file(self, file_path):
        """Point d'entrée unique : importe et convertit."""
        raw = self.importer.read_excel(file_path)
        self.database = DataConverter.from_legacy(raw)
        self.storage.export(self.database)

    def get_exercise_names(self, database):
        return [ex["name"] for ex in database["exercise_library"].values()]

    def get_sessions(self, database):
        return database["sessions"]