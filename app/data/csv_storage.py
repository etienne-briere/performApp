

from collections import defaultdict
import csv
import datetime
import os


class CsvStorage:

    def __init__(self, folder_path):
        self.folder_path = folder_path
    
    def export(self, database):
        """
        Exporte la base de données en CSV dans un dossier.
        - sessions.csv
        - bodyweight.csv
        - exercise_library.csv

        :param database: dict contenant 'exercise_library', 'sessions', 'bodyweight_history'
        """
        # Créer le dossier s'il n'existe pas
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)

        # -----------------------------
        # 1️⃣ Exporter exercise_library
        # -----------------------------
        lib_file = os.path.join(self.folder_path, "exercise_library.csv")
        with open(lib_file, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["exercise_id", "name", "muscle_group", "primary_group", "secondary_group", "type"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for ex_id, ex_data in database["exercise_library"].items():
                writer.writerow({
                    "exercise_id": ex_id,
                    "name": ex_data.get("name",""),
                    "muscle_group": ex_data.get("muscle_group",""),
                    "primary_group": ",".join(ex_data.get("primary_group",[])),
                    "secondary_group": ",".join(ex_data.get("secondary_group",[])),
                    "type": ex_data.get("type","")
                })

        # -----------------------------
        # 2️⃣ Exporter sessions
        # -----------------------------
        sessions_file = os.path.join(self.folder_path, "sessions.csv")
        with open(sessions_file, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["date", "exercise_name", "set_index", "reps", "weight", "tempo", "rest", "rpe", "notes"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for session in database["sessions"]:
                date_str = session["date"].strftime("%Y-%m-%d")
                for ex in session["exercises"]:
                    ex_name = database["exercise_library"][ex["exercise_id"]]["name"]
                    rpe = ex.get("rpe","")
                    notes = ex.get("notes","")
                    for i, s in enumerate(ex["sets"], start=1):
                        writer.writerow({
                            "date": date_str,
                            "exercise_name": ex_name,
                            "set_index": i,
                            "reps": s.get("r",""),
                            "weight": s.get("w",""),
                            "tempo": s.get("tempo",""),
                            "rest": s.get("rest",""),
                            "rpe": rpe,
                            "notes": notes
                        })

        # -----------------------------
        # 3️⃣ Exporter bodyweight_history
        # -----------------------------
        bodyweight_file = os.path.join(self.folder_path, "bodyweight.csv")
        with open(bodyweight_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "weight"])
            writer.writeheader()
            for rec in database.get("bodyweight_history", []):
                writer.writerow({
                    "date": rec["date"].strftime("%Y-%m-%d"),
                    "weight": rec["weight"]
                })

        print(f"Export terminé dans le dossier : {self.folder_path}")
    
    def load(self) -> dict:
        """
        Importe la base de données depuis les CSV d'un dossier et reconstruit la structure complète.

        :param folder_path: dossier contenant exercise_library.csv, sessions.csv, bodyweight.csv
        :return: database dict
        """

        database = {
            "exercise_library": {},
            "sessions": [],
            "bodyweight_history": []
        }

        # -----------------------------
        # 1️⃣ Charger exercise_library
        # -----------------------------
        lib_file = os.path.join(self.folder_path, "exercise_library.csv")
        with open(lib_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ex_id = int(row["exercise_id"])
                database["exercise_library"][ex_id] = {
                    "name": row.get("name",""),
                    "muscle_group": row.get("muscle_group",""),
                    "primary_group": row.get("primary_group","").split(",") if row.get("primary_group") else [],
                    "secondary_group": row.get("secondary_group","").split(",") if row.get("secondary_group") else [],
                    "type": row.get("type","")
                }

        # -----------------------------
        # 2️⃣ Charger sessions
        # -----------------------------
        sessions_file = os.path.join(self.folder_path, "sessions.csv")
        # On utilise un dict temporaire pour regrouper par date et par exercice
        sessions_dict = defaultdict(lambda: {"date": None, "exercises": defaultdict(lambda: {"exercise_id": None, "sets": [], "rpe": "", "notes": ""})})

        with open(sessions_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = datetime.strptime(row["date"], "%Y-%m-%d")
                ex_name = row["exercise_name"]
                # Trouver l'exercise_id
                ex_id = next((eid for eid, ed in database["exercise_library"].items() if ed["name"] == ex_name), None)
                if ex_id is None:
                    continue  # skip si exercice absent dans library

                # Créer session
                session = sessions_dict[date]
                session["date"] = date
                ex_data = session["exercises"][ex_id]
                ex_data["exercise_id"] = ex_id
                ex_data["rpe"] = row.get("rpe","")
                ex_data["notes"] = row.get("notes","")
                # Ajouter set
                ex_data["sets"].append({
                    "r": float(row.get("reps",0)),
                    "w": float(row.get("weight",0)),
                    "tempo": row.get("tempo",""),
                    "rest": row.get("rest","")
                })

        # Transformer en liste triée
        for date in sorted(sessions_dict.keys()):
            session = sessions_dict[date]
            # Convertir exercises dict en liste
            session["exercises"] = list(session["exercises"].values())
            database["sessions"].append(session)

        # -----------------------------
        # 3️⃣ Charger bodyweight_history
        # -----------------------------
        bodyweight_file = os.path.join(self.folder_path, "bodyweight.csv")
        if os.path.exists(bodyweight_file):
            with open(bodyweight_file, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    database["bodyweight_history"].append({
                        "date": datetime.strptime(row["date"], "%Y-%m-%d"),
                        "weight": float(row["weight"])
                    })

        print(f"Import terminé depuis le dossier : {self.folder_path}")
        
        return database