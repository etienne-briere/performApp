# from app.core.supabase_client import supabase
from kivymd.toast import toast

class AuthService:

    @staticmethod
    def signup_user(email, password):

        if not email or not password:
            toast("Email et mot de passe requis")
            return

        try:
            result = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            return result

        except Exception as e:
            toast(str(e))
            return None


    @staticmethod
    def login(email, password):
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response.user, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def logout():
        supabase.auth.sign_out()

    @staticmethod
    def current_user():
        return supabase.auth.get_user()
