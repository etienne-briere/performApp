from datetime import datetime

# from app.core.supabase_client import supabase

class PerformanceService:

    @staticmethod
    def insert_performance(user_id, exercise_name, perf_dict):
        """
        Enregistre une performance dans Supabase
        """

        date_value = perf_dict["Date"]

        # ✅ Conversion datetime → string ISO
        if isinstance(date_value, datetime):
            date_value = date_value.date().isoformat()
        elif isinstance(date_value, str):
            date_value = date_value  # déjà OK

        payload = {
            "user_id": user_id,
            "exercise_name": exercise_name,
            "Date séance": date_value,
            "Kg": perf_dict["Kg"],
            "Etat": perf_dict["Etat"],
            "Notes": perf_dict["Notes"],
        }

        # Séries dynamiques (S1, S2, ...)
        for key, value in perf_dict.items():
            if key.startswith("S"):
                payload[key] = value

        # Calcul total
        series = [v for k, v in perf_dict.items() if k.startswith("S") and v is not None]
        payload["Total"] = sum(series) if series else 0

        print("PAYLOAD SUPABASE:", payload)

        result = supabase.table("performances").insert(payload).execute()

        return result
