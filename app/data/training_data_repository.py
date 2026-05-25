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
        self.storage = app.storage
        
        # Initialisation de la base de données en mémoire et du stockage
        self.database = {"exercise_library": {}, "sessions": [], "body_weight_history": []}

    def load_from_file(self, raw):
        """Point d'entrée unique : importe et convertit."""

        # Convertir
        convert = DataConverter()
        self.database = convert.from_legacy(raw)

        # Sauvegarder
        # self.storage.export(self.database)

        # Mettre à jour l'état global
        self.exercise_names = self.get_exercise_names(self.database)

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
                        "id": session.get("id"),
                        "date": date,
                        "sets": ex["sets"],
                        "rpe": ex["rpe"],
                        "notes": ex["notes"]
                    })

        return history
    
    def get_exercise_from_session(self, session, exercise_id):
        return next(
            (e for e in session["exercises"] if e["exercise_id"] == exercise_id),
            None
        )
    
    def generate_session_id(self):
        """Génère un nouvel ID unique de session."""

        if not self.database["sessions"]:
            return 1

        return max(s["id"] for s in self.database["sessions"]) + 1
    
    def create_session(self, date, exercise_id, sets, rpe=None, notes=""):
        """Créer une nouvelle session."""

        new_session = {
            "id": self.generate_session_id(),
            "date": date,
            "exercises": [
                {
                    "exercise_id": exercise_id,
                    "sets": sets,
                    "rpe": rpe,
                    "notes": notes
                }
            ]
        }

        self.database["sessions"].append(new_session)

        self._refresh_after_update()

        return new_session
    
    def update_session(self,session_id,exercise_id,date,sets,rpe=None,notes=""):
        """Met à jour un exercice dans une session."""

        session = next(
            (
                s for s in self.database["sessions"]
                if s["id"] == session_id
            ),
            None
        )

        if not session:
            return False

        # mise à jour date
        session["date"] = date

        # retrouver exercice
        ex = self.get_exercise_from_session(
            session,
            exercise_id
        )

        if not ex:
            return False

        # update exercice
        ex["sets"] = sets
        ex["rpe"] = rpe
        ex["notes"] = notes

        self._refresh_after_update()

        return True

    def save_database(self, folder_path=None):
        """
        Sauvegarde vers CSV.
        """

        try:

            # si on change de dossier dynamiquement
            if folder_path:
                self.storage = CsvStorage(folder_path)

            self.storage.export(self.database)

            return True

        except Exception as e:
            print(f"save_database error: {e}")
            return False
        
    def delete_exercise_from_session(self, session_id, exercise_id):
        """Supprime un exercice spécifique d'une session."""
        
        for s in self.database["sessions"]:
            # if s["date"] == session["date"]:  # 🔥 clé de matching
            if s["id"] == session_id:
                s["exercises"] = [
                    ex for ex in s["exercises"]
                    if ex["exercise_id"] != exercise_id
                ]

                # Si plus aucun exercice → supprimer la session
                if not s["exercises"]:
                    self.database["sessions"].remove(s)

                break

        self._refresh_after_update()
    
    def _refresh_after_update(self):
        app = App.get_running_app()

        if app.selected_exercise:
            app.exercise_history = self.get_exercise_history(
                app.selected_exercise,
                self.database
            )

    def on_exercise_names(self, instance, value):
        """on_<property> = réaction automatique à un changement d’état de <property>"""
        if value:
            app = App.get_running_app()

            # Si aucun exercice n'est encore sélectionné, sélectionner le 1er de la liste pour déclencher l’affichage de l’historique
            if not app.selected_exercise:
                app.selected_exercise = value[0] # déclenche la mise à jour de l’historique via on_selected_exercise dans app.py