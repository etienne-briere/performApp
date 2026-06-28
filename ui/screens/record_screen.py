from datetime import datetime, time
from kivy.app import App


from kivy.metrics import sp, dp
from kivymd.uix.button import MDIconButton, MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField

from kivymd.toast import toast
from kivy.clock import Clock
from kivy.utils import platform
from kivy.properties import BooleanProperty, NumericProperty, StringProperty, ObjectProperty
from kivy.uix.image import AsyncImage

if platform == "android":
    from jnius import autoclass, cast
    from android import activity

from plyer import filechooser
import os
import threading
from openpyxl import Workbook
from config import SERIE_COUNT, SMILEY_DATA, SMILEY_ICON_SIZE, FONT_SIZE_BUTTON, FONT_SIZE_BUTTON2, FONT_STYLE_SUBTITLE1, FONT_STYLE_SUBTITLE2, ICON_SIZE

class RecordScreen(MDScreen):

    # Properties pour l'UI
    date_activity = ObjectProperty(datetime.today()) # date de la séance
    date_activity_str = ObjectProperty(datetime.today().strftime("%d/%m/%Y")) # date de la séance
    font_size_button = NumericProperty(FONT_SIZE_BUTTON) # taille du texte des boutons
    font_size_button2 = NumericProperty(FONT_SIZE_BUTTON2) # taille du texte des boutons secondaires
    font_style_subtitle1 = StringProperty(FONT_STYLE_SUBTITLE1) # style du texte des sous-titres
    font_style_subtitle2 = StringProperty(FONT_STYLE_SUBTITLE2) # style du texte des titres des encadrés
    icon_size = NumericProperty(ICON_SIZE) # taille des icônes
    loader_icon_source = StringProperty("assets/loading.gif")
    success_icon_source = StringProperty("assets/congratulations.gif")

    def __init__(self, **kwargs):
        super().__init__(**kwargs) # super() appelle _init_ de la class parent

        # --- Initialisation des variables ---
        self.selected_rpe = None
        self.smiley_buttons = []
        self.all_exercise_dfs = dict()
        self.series_inputs = [] # stockage des champs des séries

    def on_kv_post(self, base_widget):
        """
        Appelé automatiquement quand le kv est chargé
        et que les ids sont disponibles.
        """
        # Ajouter 3 séries par défaut
        for i in range(SERIE_COUNT):
            self.add_serie_input()
        
        # Créer les boutons de smiley dans l'UI
        for smiley_data in SMILEY_DATA:

            btn = MDIconButton(
                icon=smiley_data["icon"],
                theme_icon_color="Custom",
                text_color=smiley_data["color"],
                icon_size=SMILEY_ICON_SIZE,
                size_hint=(1, None),
                on_release=lambda inst, rpe=smiley_data["rpe"]: self.on_smiley_select(rpe)
            )

            self.smiley_buttons.append(btn)
            self.ids.smiley_layout.add_widget(btn)

    def on_pre_enter (self):
        """
        Exécuter juste avant que l'écran devienne visible.
        """
        
        app = App.get_running_app()

        # Managers
        self.importer = app.importer

        # Si on vient de la view en mode édition, charger les données de la session à modifier
        if app.edit_mode and app.session_to_edit:
            self.load_session_for_edit(app.session_to_edit)
    
    def on_leave(self):
        """
        Exécuter quand on quitte l'écran.
        """

        # Réinitialiser le mode édition
        app = App.get_running_app()
        app.edit_mode = False
        app.session_to_edit = None
    
    def load_session_for_edit(self, session):
        '''Charger les données d'une session existante pour modification.'''

        app = App.get_running_app()

        exercise_id = app.repo.get_exercise_id(
            app.selected_exercise,
            app.repo.database
        )

        ex = app.repo.get_exercise_from_session(session, exercise_id)

        if not ex:
            return

        # Mise à jour de l'UI avec les données de la session
        # --- date ---
        self.date_activity = session["date"]
        self.date_activity_str = str(session["date"].date().strftime("%d/%m/%Y"))

        # --- poids ---
        self.ids.weight_input.text = str(ex["sets"][0]["w"]) if ex["sets"] else ""

        # --- rpe ---
        rpe_value = ex.get("rpe", None)
        if isinstance(rpe_value, str):  # ancien format : nom de l'icône du smiley
            rpe_value = self.get_rpe_from_smiley(rpe_value)
        self.on_smiley_select(rpe_value)

        # --- notes ---
        self.ids.notes_input.text = ex.get("notes", "")

        # --- sets ---
        nb_serie = len(ex["sets"])

        # Ajouter les champs manquants
        while len(self.series_inputs) < nb_serie:
            self.add_serie_input()

        # Supprimer les champs en trop
        while len(self.series_inputs) > nb_serie:
            self.remove_serie_input()

        # Remplir les reps
        for i, set_data in enumerate(ex["sets"]):
            self.series_inputs[i].text = str(set_data["r"])

    def show_date_picker(self, instance):
        """
        Ouvre une boîte de Dialog pour la sélection d'une date.
        """
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_date_save)
        date_dialog.open()

    def on_date_save(self, instance, value, date_range):
        """
        Sauvegarde la date choisie.
        :param value: valeur de la date
        :return:
        """
        # Ajoute l'heure à la date choisi (00:00:00)
        self.date_activity = datetime.combine(value, time.min)
        # convertir value (aaaa-mm-jj) en jj/mm/aaaa
        self.ids.date_button.text = value.strftime("%d/%m/%Y")

    def update_exercise_content(self, selected_exercise_name):
        """
        MAJ du widget du choix de l'exercice.
        """
        self.ids.exercise_menu_button.text = selected_exercise_name
        self.ids.exercise_menu_button.line_color = "white"

    def reset_exercise_menu_button (self):
        """
        Réinitialiser le texte du bouton d'exercice.
        """

        # Contour du bouton en rouge
        self.ids.exercise_menu_button.line_color = "red"

        if len(self.app.view.menu_name_exercise_item) <= 1:
            self.ids.exercise_menu_button.text = "Ajoute un exercice"
        else :
            self.ids.exercise_menu_button.text = "Sélectionne un exercice"

    def remove_history_content(self):
        """
        Retirer l'encadré du rappel de perf et l'accès à l'historique complet.
        """

        # Retirer accès vers l'historique
        self.ids.history_content.height = 0
        self.ids.history_content.opacity = 0
        self.ids.history_content.disabled = True  # désactive les clics

        # Retirer accès vers l'historique sur l'écran view
        self.app.view.remove_history_content()

        # Initialistion de l'entrée du poids
        self.ids.weight_input.text = ""

    def update_last_perfs_card(self, dict_exo):
        """
        MAJ de l'encadré de la dernière perf.
        :param dict_exo: liste de dict de chaque enregistrement de l'exercice
        :return:
        """
        # Si pas d'enregistrement
        if len(dict_exo) == 0:
            self.remove_history_content()
            return

        # Dernière perf = 1ère dans la liste
        last_perf = dict_exo[0]

        # Modifier les Labels Date + Kg
        self.ids.date_label.text = last_perf["Date séance"]
        self.ids.kg_label.text = str(last_perf['Kg'])

        # Récupérer les colonnes de séries ("S1", "S2", ...)
        reps = [str(v) for k, v in last_perf.items() if k.startswith("S") and v is not None]

        # Modifier le label Reps
        self.ids.reps_label.text = "  |  ".join(reps)

        # Modifier l'icon de l'état de forme
        if "Etat" in last_perf and last_perf['Etat'] is not None :
            self.ids.etat_icon.icon = last_perf['Etat']
            self.ids.etat_icon.text_color = self.get_smiley_color(last_perf['Etat'])
        else :
            self.ids.etat_icon.icon = "emoticon-neutral-outline"
            self.ids.etat_icon.text_color = "gray"

        # MAJ de l'entrée du poids
        self.ids.weight_input.text = self.ids.kg_label.text

        # Apparition de l'accès vers l'historique complet
        self.ids.history_content.height =  self.ids.history_content.minimum_height
        self.ids.history_content.opacity = 1
        self.ids.history_content.disabled = False # active les clics
        self.app.view.add_history_content()

    def add_serie_input(self, instance=None):
        """
        Ajouter une nouvelle entrée de série.
        """
        # Si le bouton est présent on le retire pour insérer la nouvelle série juste au-dessus
        if self.ids.buttons_serie_content in self.ids.zone_3_record_content.children:
            self.ids.zone_3_record_content.remove_widget(self.ids.buttons_serie_content)

        serie_number = len(self.series_inputs) + 1
        serie_input = MDTextField(
            hint_text=f"Série {serie_number}",
            helper_text="Entre le nombre de répétitions",
            icon_left="layers",
            helper_text_mode="on_focus",
            mode="rectangle",
            size_hint=(0.9, 0.2),
            pos_hint={"center_x": 0.5},
            input_filter="float",
            text_color_focus="white",  # couleur du texte entrant
            hint_text_color_focus=(1, 0.6, 0.2, 1),  # couleur du petit texte en haut en focus
            line_color_focus=(1, 0.5, 0, 1),  # contour plus cintrasté au focus
            icon_left_color_focus=(1, 0.65, 0.2, 1),
            helper_text_color_focus=(1, 0.55, 0.1, 1)
        )

        # Stocke le champ puis l'ajoute dans la zone
        self.series_inputs.append(serie_input)
        self.ids.zone_3_record_content.add_widget(serie_input)

        # Ré-ajoute les boutons au layout
        self.ids.zone_3_record_content.add_widget(self.ids.buttons_serie_content)

    def remove_serie_input(self, instance=None):
        """
        Retirer la dernière série ajoutée.
        """
        if self.series_inputs:
            last_input = self.series_inputs.pop()  # supprime de la liste
            self.ids.zone_3_record_content.remove_widget(last_input)  # supprime de l’UI

    def reset_series(self):
        """
        Réinitialiser les zones d'entrée des séries.
        """
        for serie in self.series_inputs:
            serie.text = ""

    def reset_inputs (self):
        """
        Réinitialiser les entrées.
        """

        self.reset_series()
        self.reset_smiley_btn()
        self.ids.notes_input.text = ""

    def on_smiley_select(self, rpe_value):
        """
        Met en évidence le smiley sélectionné en le gardant coloré et en grisant les autres.
        :param index: index du smiley cliqué dans la liste smiley_data
        """
       
        for btn, smiley_data in zip(self.smiley_buttons, SMILEY_DATA):

            if smiley_data["rpe"] == rpe_value:
                btn.text_color = smiley_data["color"]
            else:
                btn.text_color = (0.6, 0.6, 0.6, 1)

        self.selected_rpe = rpe_value

    def reset_smiley_btn(self):
        """
        Réinitialiser la zone d'état de forme.
        """
        for btn, smiley_data in zip(self.smiley_buttons, SMILEY_DATA):
            btn.text_color = smiley_data["color"]
    
    def get_smiley_from_rpe(self,rpe):
        return next(
            s for s in SMILEY_DATA
            if s["rpe"] == rpe
        )
    
    def get_rpe_from_smiley(self,smiley):
        return next(
            s["rpe"] for s in SMILEY_DATA
            if s["icon"] == smiley
        )

    # CODE MORT (ancienne architecture) : SMILEY_DATA est désormais une liste de dicts
    # {rpe, icon, color}, donc "for name, color in SMILEY_DATA" plante (ValueError:
    # too many values to unpack). Seul appelant : update_last_perfs_card, lui-même
    # uniquement appelé depuis le bloc legacy commenté dans view_screen.py (self.app.profile).
    # def get_smiley_color(self, icon_name):
    #     for name, color in SMILEY_DATA:
    #         if name == icon_name:
    #             return color
    #     # return None  # si non trouvé

    def save_activity(self, instance=None):
        """
        Lancer la sauvegarde de la session d'activité.
        :param instance:
        :return:
        """
        app = App.get_running_app()

        # Capturer edit_mode/session_to_edit tout de suite : on_leave() (déclenché si
        # l'utilisateur change d'écran avant la fin du thread) les réinitialise, ce qui
        # ferait basculer _save_activity sur une création au lieu d'une mise à jour.
        edit_mode = app.edit_mode
        session_to_edit = app.session_to_edit

        exercise_id = app.repo.get_exercise_id(app.selected_exercise, app.repo.database)
        exclude_id = session_to_edit["id"] if edit_mode and session_to_edit else None

        conflict_session = app.repo.find_session_by_date_and_exercise(
            self.date_activity, exercise_id, exclude_id=exclude_id
        )

        if conflict_session:
            self.show_duplicate_dialog(conflict_session, edit_mode, session_to_edit)
            return

        self.start_save_thread(edit_mode, session_to_edit)

    def show_duplicate_dialog(self, conflict_session, edit_mode, session_to_edit):
        """
        Affiche un choix à l'utilisateur quand une séance existe déjà à la même date
        pour le même exercice : écraser l'ancienne ou en créer une nouvelle quand même.
        """
        date_str = conflict_session["date"].strftime("%d/%m/%Y")

        self.duplicate_dialog = MDDialog(
            title="Séance déjà existante",
            text=f"Une séance pour cet exercice existe déjà le {date_str}. Que veux-tu faire ?",
            buttons=[
                MDFlatButton(
                    text="ANNULER",
                    on_release=lambda x: self.duplicate_dialog.dismiss()
                ),
                MDFlatButton(
                    text="CRÉER UNE NOUVELLE",
                    on_release=lambda x: self.resolve_duplicate(False, conflict_session, edit_mode, session_to_edit)
                ),
                MDRaisedButton(
                    text="ÉCRASER L'ANCIENNE",
                    md_bg_color="red",
                    on_release=lambda x: self.resolve_duplicate(True, conflict_session, edit_mode, session_to_edit)
                ),
            ],
        )
        self.duplicate_dialog.open()

    def resolve_duplicate(self, overwrite, conflict_session, edit_mode, session_to_edit):
        """
        Applique le choix de l'utilisateur face à une séance en conflit.
        :param overwrite: True pour écraser la séance en conflit, False pour en créer une nouvelle quand même
        """
        self.duplicate_dialog.dismiss()

        if overwrite:
            app = App.get_running_app()

            # Si on éditait une AUTRE séance que celle en conflit, on la supprime pour
            # ne pas laisser un doublon résiduel après avoir basculé sur le conflit.
            if edit_mode and session_to_edit and session_to_edit["id"] != conflict_session["id"]:
                exercise_id = app.repo.get_exercise_id(app.selected_exercise, app.repo.database)
                app.repo.delete_exercise_from_session(session_to_edit["id"], exercise_id)

            edit_mode = True
            session_to_edit = conflict_session

        self.start_save_thread(edit_mode, session_to_edit)

    def start_save_thread(self, edit_mode, session_to_edit):
        # Afficher le loader
        self.ids.loader_gif.opacity = 1

        # Lancer le thread de sauvegarde
        threading.Thread(target=self._save_activity, args=(edit_mode, session_to_edit), daemon=True).start()

    def _save_activity(self, edit_mode, session_to_edit):

        app = App.get_running_app()

        # -----------------------------
        # exercise_id (FIX CRITIQUE)
        # -----------------------------
        exercise_id = app.repo.get_exercise_id(
            app.selected_exercise,
            app.repo.database
        )

        # -----------------------------
        # weight safe
        # -----------------------------
        weight = self.ids.weight_input.text.strip()
        weight = float(weight) if weight else None

        # -----------------------------
        # sets
        # -----------------------------
        sets = []

        for reps_input in self.series_inputs:
            reps = reps_input.text.strip()

            if reps:
                sets.append({
                    "w": weight,
                    "r": int(reps)
                })

        # -----------------------------
        # MODE EDITION
        # -----------------------------
        if edit_mode:

            app.repo.update_session(
                session_id=session_to_edit["id"],
                exercise_id=exercise_id,
                date=self.date_activity,
                sets=sets,
                rpe=self.selected_rpe,
                notes=self.ids.notes_input.text
            )

        # -----------------------------
        # MODE CREATION
        # -----------------------------
        else:

            app.repo.create_session(
                date=self.date_activity,
                exercise_id=exercise_id,
                sets=sets,
                rpe=self.selected_rpe,
                notes=self.ids.notes_input.text
            )

        # -----------------------------
        # SAVE
        # -----------------------------
        app.repo.save_database()

        # -----------------------------
        # RESET MODE
        # -----------------------------
        app.edit_mode = False
        app.session_to_edit = None

        # -----------------------------
        # UI feedback
        # -----------------------------
        Clock.schedule_once(self.finish_save_ui)
    
    def finish_save_ui(self, dt):

        self.ids.loader_gif.opacity = 0

        # self.ids.success_gif.opacity = 1

    # def _save_activity(self, instance=None):
    #     """
    #     (Tread) Enregistrer la nouvelle perf dans le dictionnaire.
    #     """
            
    #     # Liste des activités enregistrées de l'exercice cible
    #     dict_exo = self.app.profile.all_exercise_dict[self.app.view.selected_exercise_name]

    #     # --- Nouvelle ligne de données ---
    #     new_row = {
    #         "Date": self.date_activity,
    #         "Kg": float(self.ids.weight_input.text),
    #         "Total": None,
    #         "Etat": self.selected_rpe,
    #         "Notes": self.ids.notes_input.text,
    #     }

    #     # --- Nombre de séries ---
    #     nb_serie = len(self.ids.zone_3_record_content.children) - 3

    #     # Ajouter dynamiquement les colonnes de séries
    #     for i in range(nb_serie):
    #         repetitions = float(self.series_inputs[i].text) if self.series_inputs[i].text else None
    #         new_row[f"S{i + 1}"] = repetitions

    #     # Vérifier que l'exercice cible existe et est bien une liste
    #     if not isinstance(self.app.profile.all_exercise_dict.get(self.app.view.selected_exercise_name), list):
    #         self.app.profile.all_exercise_dict[self.app.view.selected_exercise_name] = []

    #     # Ajouter la nouvelle performance
    #     dict_exo.append(new_row)

    #     # Réenregistrer
    #     self.app.profile.all_exercise_dict[self.app.view.selected_exercise_name] = dict_exo


    def open_file_manager_export(self, *args):
        """
        Gère l'export du fichier en fonction de la plateforme.
        """
        print("Préparation export…")

        if platform == "android":
            self.share_file()
        else:
            filechooser.choose_dir(
                title="Choisir un dossier",
                on_selection=self.select_export_folder
            )

    def share_file(self):
        """
        Partage le fichier avec les options android.
        :return:
        """
        try:
            # 🔹 Nom du fichier à partager
            filename = f"performances_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            # 🔹 Chemin dans le stockage interne de l'app
            from android.storage import app_storage_path
            app_path = app_storage_path()
            file_path = os.path.join(app_path, filename)

            wb = Workbook()

            for exercise, rows in self.app.profile.all_exercise_dict.items():
                if not rows:
                    continue
                ws = wb.create_sheet(title=exercise[:31])
                headers = list(rows[0].keys())
                ws.append(headers)
                for row in rows:
                    ws.append([row.get(h) for h in headers])

            # Supprimer la feuille par défaut
            if "Sheet" in wb.sheetnames:
                wb.remove(wb["Sheet"])

            wb.save(file_path)
            print(f"✅ Fichier mis à jour : {file_path}")

            # 🔹 Import des classes Java nécessaires
            File = autoclass('java.io.File')
            Intent = autoclass('android.content.Intent')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            FileProvider = autoclass('androidx.core.content.FileProvider')

            # 🔹 Préparer le fichier à partager
            file = File(file_path)
            authority = f"{PythonActivity.mActivity.getPackageName()}.fileprovider"
            print(f"📦 Authority : {authority}")
            uri = FileProvider.getUriForFile(PythonActivity.mActivity, authority, file)

            # 🔹 Créer l’intent de partage
            intent = Intent(Intent.ACTION_SEND)
            intent.setType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            intent.putExtra(Intent.EXTRA_STREAM, cast('android.os.Parcelable', uri))
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

            # ✅ Conversion du titre Python -> Java CharSequence correctement
            String = autoclass('java.lang.String')
            title_java = String("Partager le fichier Excel")
            title = cast('java.lang.CharSequence', title_java)

            # 🔹 Créer un "chooser"
            chooser = Intent.createChooser(intent, title)

            # 🔹 Démarrer l’intent
            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.startActivity(chooser)

            print(f"✅ Partage du fichier : {file_path}")

        except Exception as e:
            print(f"❌ Erreur de partage : {e}")

    def select_export_folder(self, path_list):
        """
        Exporte le fichier dans le dossier d'export choisi (si Windows).
        :param path_list: chemin vers le dossier choisi
        """
        if not path_list:
            toast("Aucun dossier sélectionné.")
            return

        chosen_path = path_list[0]
        if not os.path.isdir(chosen_path):
            chosen_path = os.path.expanduser("~/Documents")

        self.export_folder = chosen_path
        print(f"dossier d'export : {self.export_folder}")
        self.open_filename_dialog()

    def open_filename_dialog(self):
        """
        Ouvre un popup pour saisir le nom du fichier .xlsx.
        """
        self.filename_input = MDTextField(
            hint_text="Nom du fichier",
            text="performances"
        )

        self.dialog = MDDialog(
            title="Nom du fichier",
            type="custom",
            content_cls=self.filename_input,
            buttons=[
                MDRaisedButton(
                    text="ANNULER",
                    on_release=lambda x: self.dialog.dismiss(),
                    md_bg_color = "red"
                ),
                MDRaisedButton(
                    text="VALIDER",
                    on_release=self.confirm_export,
                    md_bg_color = "green"
                ),
            ],
        )
        self.dialog.open()

    def confirm_export(self, *args):
        """
        Confirmer l'export du fichier.
        """
        self.dialog.dismiss()

        filename = self.filename_input.text.strip()
        if not filename:
            toast("Nom de fichier invalide.")
            return

        final_path = os.path.join(self.export_folder, filename + ".xlsx")
        print(f"chemin final d'export : {final_path}")

        try:
            self.export_all_exercises(final_path)
            toast(f"Export réussi : {final_path}")
        except Exception as e:
            toast(f"Erreur export : {e}")
            print(f"Erreur export : {e}")

    def export_all_exercises(self, filename):
        """
        Exporte le dictionnaire complet vers un fichier .xlsx.
        """
        try:
            wb = Workbook()

            for exercise, rows in self.app.profile.all_exercise_dict.items():
                if not rows:
                    continue
                ws = wb.create_sheet(title=exercise[:31])
                headers = list(rows[0].keys())
                ws.append(headers)
                for row in rows:
                    ws.append([row.get(h) for h in headers])

            # ✅ Supprimer la feuille vide par défaut
            if "Sheet" in wb.sheetnames:
                wb.remove(wb["Sheet"])

            # ✅ 1) Sauvegarde dans stockage interne/app
            wb.save(filename)
            print(f"✅ Fichier exporté ici : {filename}")

            toast(f"Exporté : {filename}")

        except Exception as e:
            toast(f"Erreur export : {e}")