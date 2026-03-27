from app.data.csv_storage import CsvStorage

class DataConverter:

    def from_legacy(self, old_dict) -> dict:
        """Convertit l'ancien format {exercice: [records]} vers le nouveau schéma.
        database = {
            "exercise_library": {id: {name, muscle_group, primary_group, secondary_group, type}},
            "sessions": [
                {
                    "date": datetime,
                    "exercises": [
                        {
                            "exercise_id": id,
                            "sets": [{"r": reps, "w": weight}, ...]
                        }
                    ]
                }
            ]
        }"""
        
        database = {
            "exercise_library": {},
            "sessions": [],
            "body_weight_history": []  # à compléter si tu as des données de poids corporel
        }

        # --- 1️⃣ Créer exercise_library ---
        exercise_ids = {}  # mapping name -> id
        for i, ex_name in enumerate(old_dict.keys(), start=1):
            exercise_ids[ex_name] = i

            # Ici tu peux personnaliser les infos sur chaque exercice
            # Pour l'instant on met des valeurs par défaut pour muscle_group, primary, secondary, type
            database["exercise_library"][i] = {
                "name": ex_name,
                "muscle_group": "Unknown",     # à compléter selon tes exercices
                "primary_group": [],           # muscles principaux
                "secondary_group": [],         # muscles secondaires
                "type": "bodyweight"           # ou "barbell" si connu
            }

        # --- 2️⃣ Créer sessions ---
        # On va créer une session par date
        sessions_dict = {}  # temporaire pour regrouper les exercices par date

        for ex_name, records in old_dict.items():
            ex_id = exercise_ids[ex_name]

            for record in records:
                date = record["Date"]
                rpe = record["Etat"] if "Etat" in record else ""
                notes = record["Notes"] if "Notes" in record else ""


                # Créer la session si elle n'existe pas encore
                if date not in sessions_dict:
                    sessions_dict[date] = {
                        "date": date,
                        "exercises": []
                    }

                # Créer les sets
                sets = []
                for k, v in record.items():
                    if k.startswith("S") and isinstance(v, (int, float)):
                        sets.append({"r": v, "w": record["Kg"], "tempo":"", "rest": ""})

                # Ajouter l'exercice à la session
                sessions_dict[date]["exercises"].append({
                    "exercise_id": ex_id,
                    "sets": sets,
                    "rpe": rpe,
                    "notes": notes
                })

        # Trier par date
        database["sessions"] = sorted(
            sessions_dict.values(),
            key=lambda x: x["date"]
        )

        storage = CsvStorage(folder_path="my_training_data")
        storage.export(database)
    
        return database