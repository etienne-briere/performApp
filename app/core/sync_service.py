from app.data.performance_repository import PerformanceRepository

class SyncService:

    def __init__(self, app):
        self.app = app

    def load_user_data(self):
        user_id = self.app.profile.user_id
        print(f"user_id : {user_id}")

        performances = PerformanceRepository.fetch_all(user_id)
        print(f"performances : {performances}")

        # Conversion DB → dict Python
        self.app.profile.all_exercise_dict = self.format_data(performances)

        # Récupérer le nom de la première feuille
        first_key = list(self.app.profile.all_exercise_dict.keys())[0]

        print(f"Dictionnaire complet importé : {self.app.profile.all_exercise_dict}")

        # Ajouter dans l'onglet [VISUALISATION]
        self.app.view.update_exercise_menu_button_text(first_key)
        self.app.view.select_exercise(first_key)

    def format_data(self, rows):
        result = {}
        for row in rows:
            exo = row["exercise_name"]
            result.setdefault(exo, []).append(row)
        return result
