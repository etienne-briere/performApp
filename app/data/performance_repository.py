# from app.core.supabase_client import supabase

class PerformanceRepository:

    @staticmethod
    def fetch_all(user_id):
        return supabase.table("performances") \
            .select("*") \
            .eq("user_id", user_id) \
            .execute().data

    @staticmethod
    def insert(perf_dict):
        supabase.table("performances").insert(perf_dict).execute()
