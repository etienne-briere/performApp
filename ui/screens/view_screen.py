import threading

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivymd.uix.screen import MDScreen

from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp, sp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton, MDRectangleFlatIconButton
from kivymd.toast import toast
from kivy.clock import Clock
from kivy.properties import BooleanProperty, NumericProperty, StringProperty, ObjectProperty


from kivy_matplotlib_widget.uix.graph_widget import MatplotFigure

from datetime import datetime, timedelta, time
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from collections import Counter
from dateutil.relativedelta import relativedelta

from app import app
from config import SERIE_COUNT, SMILEY_DATA, SMILEY_ICON_SIZE, FONT_SIZE_BUTTON, FONT_SIZE_BUTTON2, FONT_STYLE_SUBTITLE1, FONT_STYLE_SUBTITLE2, ICON_SIZE

class ViewScreen(MDScreen): # Kivy voit cette classe et va chercher dans tous les fichiers KV un bloc qui correspond à cette classe

    # Properties pour l'UI
    font_size_button = NumericProperty(FONT_SIZE_BUTTON) # taille du texte des boutons
    font_size_button2 = NumericProperty(FONT_SIZE_BUTTON2) # taille du texte des boutons secondaires
    font_style_subtitle1 = StringProperty(FONT_STYLE_SUBTITLE1) # style du texte des sous-titres
    font_style_subtitle2 = StringProperty(FONT_STYLE_SUBTITLE2) # style du texte des titres des encadrés
    icon_size = NumericProperty(ICON_SIZE) # taille des icônes
    period_label = StringProperty("") # label de la période sélectionnée (ex: "01 Jan - 31 Jan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs) # super() appelle _init_ de la class parent

        self.dict_exo = None
        # self.menu_name_exercise_item = []
        self.menu_items = []

    def on_kv_post(self, base_widget):
        """
        Appelé automatiquement quand le kv est chargé
        et que les ids sont disponibles.
        """

        self.initialize_graph_volume()
        self.initialize_graph_perf()
    
    def on_pre_enter(self):
        app = App.get_running_app()

        # Managers
        self.importer = app.importer

        # 🔥 écouter les changements d'historique et de période
        app.bind(exercise_history=self.update_graphs)
        app.bind(selected_period=self.update_graphs)
        app.bind(time_offset=self.update_graphs)
        app.bind(selected_period=self.update_period_label)
        app.bind(time_offset=self.update_period_label)

        self.update_period_label()

        # 🔥 charger l'état actuel (important)
        if app.exercise_history:
            self.update_graphs(app, app.exercise_history)
   
    def on_leave(self):
        app = App.get_running_app()

        app.unbind(exercise_history=self.update_graphs)
        app.unbind(selected_period=self.update_graphs)

    def initialize_graph_volume(self):
        """
        Initialise le graphique du volume.
        """
        
        # Créer la figure et les axes
        self.volume_graph, self.volume_ax = plt.subplots()

        # Paramétrage du graphique
        self.volume_graph.patch.set_alpha(0.0)
        self.volume_ax.set_facecolor("none")
        self.volume_ax.margins(x=0, y=0)
        self.volume_graph.tight_layout()  # réduire l'espace perdu

        # Couleur du contour des axes
        self.volume_ax.tick_params(axis='x', colors='grey')
        for spine in self.volume_ax.spines.values():
            spine.set_color('grey')

        self.volume_ax.set_ylabel("Nombre de séances", color="grey")

        # ticks couleur
        self.volume_ax.tick_params(axis="x", colors="grey")
        self.volume_ax.tick_params(axis="y", colors="grey")

        # Associer la figure au widget MatplotFigure défini dans le kv
        self.ids.volume_graph_widget.figure = self.volume_graph

        # Désactiver les glissements
        self.ids.volume_graph_widget.touch_mode = None

    
    def initialize_graph_perf(self):
        """
        Initialise le graphique des performances.
        """

        # Créer la figure et les axes
        self.perf_graph, self.ax1_perf = plt.subplots()

        # ajout du 2ème axe y
        self.ax2_perf = self.ax1_perf.twinx()

        # Paramétrage du graphique
        self.perf_graph.patch.set_alpha(0.0)  # rend le fond de la figure transparent
        self.ax1_perf.set_facecolor("none")  # rend le fond de l’axe transparent
        self.ax1_perf.margins(x=0, y=0)  # enlève les marges inutiles autour des données
        self.perf_graph.tight_layout()  # réduire l'espace perdu

        # Couleur du contour des axes
        self.ax1_perf.tick_params(axis='x', colors='grey')
        for spine in self.ax1_perf.spines.values():
            spine.set_color('grey')

        # Associer le graphique configuré au widget
        self.ids.perf_graph_widget.figure = self.perf_graph

        # Désactiver les glissements
        self.ids.perf_graph_widget.touch_mode = None
    
    

    def select_exercise(self, name):
        """
        Modifier les widgets quand l'exercice est sélectionné.
        :param name: Nom de l'exercice
        :return:
        """
        # Associer nom de l'exo choisi à une variable
        self.selected_exercise_name = name

        # Fermer le menu si self.menu existe
        if hasattr(self, "menu"):
            self.menu.dismiss()

        # Nettoyer les données
        self.clean_all_exercises()

        # Liste des activités enregistré pour l'exercice (list de dict)
        self.dict_exo = self.app.profile.all_exercise_dict[self.selected_exercise_name]

        # Réordonner les colonnes
        self.dict_exo = self.reorder_columns(self.dict_exo)

        # Réenregistrer
        self.app.profile.all_exercise_dict[self.selected_exercise_name] = self.dict_exo

        # MAJ des widgets de l'écran "record"
        self.app.record.update_exercise_content(self.selected_exercise_name)
        self.app.record.update_last_perfs_card(self.dict_exo)
        self.app.record.reset_inputs()

        # MAJ des widgets de l'écran actuel "view"
        self.ids.exercise_menu_button.text = self.selected_exercise_name
        self.ids.exercise_menu_button.line_color = "white"

        # si pas d'activité enregistrée
        if len(self.dict_exo) == 0:
            # Retirer les widgets des graphs
            self.remove_volume_performance_graphs()

        else:
            # Ajouter les widgets des graphs
            self.add_volume_performance_graphs()

            # Tableau du résumé
            self.update_stats_resume(self.dict_exo)

            # Graphique du nombre d'activités par mois sur 1 an
            self.update_graph_volume(self.dict_exo)

            # Graphique des performances
            self.update_graph_perf(self.dict_exo)

    def update_period_label(self, *args):

        app = App.get_running_app()
        now = datetime.now()

        if app.selected_period == "7d":
            delta = timedelta(days=7)
        elif app.selected_period == "1m":
            delta = relativedelta(months=1)
        else:
            delta = relativedelta(years=1)

        end_date = now - app.time_offset * delta
        start_date = end_date - delta

        # 🔥 format dynamique
        if app.selected_period == "7d" or app.selected_period == "1m":
            text = f"{start_date.strftime('%d %b')} - {end_date.strftime('%d %b')}"
        
        else:  # 1 an
            text = f"{start_date.strftime('%B %Y')} - {end_date.strftime('%B %Y')}"

        self.period_label = text

    def update_graphs(self, *args):

        app = App.get_running_app()
        # history = app.exercise_history

        # --- TRI PAR DATE CROISSANTE (important pour les graphiques) ---
        history = sorted(app.exercise_history, key=lambda x: x["date"])
        
        # Filtrer l'historique en fonction de la période sélectionnée et du décalage temporel
        filtered_history = self.filter_history(history)

        self.update_graph_volume(filtered_history)
        self.update_graph_perf(filtered_history)


    def filter_history(self, history):

        app = App.get_running_app()

        if app.selected_period == "all":
            return history

        now = datetime.now()

        if app.selected_period == "7d":
            delta = timedelta(days=7)
        elif app.selected_period == "1m":
            delta = relativedelta(months=1)
        else:
            delta = relativedelta(years=1)

        end_date = now - app.time_offset * delta
        start_date = end_date - delta

        return [
            h for h in history
            if start_date <= h["date"] < end_date
        ]


    def update_graph_volume(self, history):

        # --- RESET ---
        self.volume_ax.clear()

        if not history:
            self.volume_ax.text(
                0.5, 0.5, "Aucune donnée",
                ha="center", va="center",
                transform=self.volume_ax.transAxes,
                color="gray"
            )
            self.volume_graph.canvas.draw_idle()
            return

        app = App.get_running_app()

        # --- CHOIX DE L’AGRÉGATION ---
        # --- 1. remplir le counter ---
        counter = Counter()

        for session in history:
            date = session["date"]

            if app.selected_period == "7d":
                key = date.strftime("%Y-%m-%d")

            elif app.selected_period == "1m":
                key = date.strftime("%Y-%W")

            else:
                key = date.strftime("%Y-%m")

            counter[key] += 1

        # --- 2. générer toutes les périodes ---
        full_keys = []
        current = min(session["date"] for session in history)
        end = max(session["date"] for session in history)

        while current <= end:
            if app.selected_period == "7d":
                key = current.strftime("%Y-%m-%d")
                current += timedelta(days=1)

            elif app.selected_period == "1m":
                key = current.strftime("%Y-%W")
                current += timedelta(weeks=1)

            else:
                key = current.strftime("%Y-%m")
                current += relativedelta(months=1)

            full_keys.append(key)

        # --- 3. reconstruire avec les 0 ---
        y_counts = [counter.get(k, 0) for k in full_keys]

        # --- 4. recréer les dates ---
        x_dates = []

        for key in full_keys:
            if app.selected_period == "7d":
                dt = datetime.strptime(key, "%Y-%m-%d")

            elif app.selected_period == "1m":
                dt = datetime.strptime(key + "-1", "%Y-%W-%w")

            else:
                dt = datetime.strptime(key, "%Y-%m")

            x_dates.append(dt)

        # --- 5. moyenne correcte ---
        moy = sum(y_counts) / len(y_counts)
       
        # --- PLOT ---
        self.volume_ax.bar(x_dates, y_counts, width=5, color="lightgreen")
        self.volume_ax.axhline(moy, linestyle="--", alpha=0.5)

        # --- STYLE ---
        self.volume_ax.set_ylabel("Nombre de séances", color="lightgreen")
        self.volume_ax.tick_params(axis="y", labelcolor="lightgreen")

        # --- FORMAT AXE X ---
        if app.selected_period == "7d":
            self.volume_ax.xaxis.set_major_locator(mdates.DayLocator())
            self.volume_ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

        elif app.selected_period == "1m":
            self.volume_ax.xaxis.set_major_locator(mdates.WeekdayLocator())
            self.volume_ax.xaxis.set_major_formatter(mdates.DateFormatter("S%W"))
        
        elif app.selected_period == "all":
            self.volume_ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.volume_ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

        else:  # 1y
            self.volume_ax.xaxis.set_major_locator(mdates.MonthLocator())
            self.volume_ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))

        self.volume_graph.autofmt_xdate()

        # --- LIMITE Y ---
        self.volume_ax.set_ylim(0, max(y_counts) + 1)

        # --- REFRESH ---
        self.volume_graph.canvas.draw_idle()

    def update_graph_perf(self, history):
        """
        Met à jour le graphique des performances en fonction de l'historique filtré.
        :param history: liste des sessions d'entraînement (filtrée selon la période)
        """

        # --- RESET GRAPH ---
        self.ax1_perf.clear()

        # Supprimer et récréer l'axe 2 pour éviter les problèmes de superposition
        self.ax2_perf.remove()
        self.ax2_perf = self.ax1_perf.twinx()

        if not history:
            self.ax1_perf.text(
                0.5, 0.5, "Aucune donnée",
                fontsize=16, color="gray",
                ha="center", va="center",
                transform=self.ax1_perf.transAxes
            )
            self.perf_graph.canvas.draw_idle()
            return

        # --- DATA PREP ---
        dates = []
        weights = []
        total_reps = []

        for session in history:
            dates.append(session["date"])

            sets = session["sets"]

            # poids moyen (ou max)
            w = max([s["w"] for s in sets]) if sets else 0
            weights.append(w)

            # total reps
            reps = sum([s["r"] for s in sets])
            total_reps.append(reps)

        # --- PLOT AXE 1 (poids soulevés) ---
        self.ax1_perf.plot(dates, weights, marker='o', color="skyblue", label="Poids (kg)")
        self.ax1_perf.fill_between(dates, weights, color="skyblue", alpha=0.2)

        # --- PLOT AXE 2 (répétitions) ---
        self.ax2_perf.plot(dates, total_reps, marker='x', linestyle='--', color="orange", label="Reps")
        self.ax2_perf.fill_between(dates, total_reps, color="orange", alpha=0.1)

        # --- STYLE AXE 1 (poids) ---
        self.ax1_perf.set_ylabel("Poids (kg)", color="skyblue")
        self.ax1_perf.tick_params(axis='y', colors='skyblue')
        
        # --- STYLE AXE 2 (répétitions) ---
        self.ax2_perf.set_ylabel("Total répétitions", color="orange")
        self.ax2_perf.tick_params(axis='y', colors='orange')

        # --- STYLE EN FONCTION DE LA PÉRIODE SÉLECTIONNÉE ---
        app = App.get_running_app()
        if app.selected_period == "7d":
            self.ax1_perf.xaxis.set_major_locator(mdates.DayLocator())
            self.ax1_perf.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

        elif app.selected_period == "1m":
            self.ax1_perf.xaxis.set_major_locator(mdates.WeekdayLocator())
            self.ax1_perf.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

        elif app.selected_period == "all":
            self.ax1_perf.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.ax1_perf.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

        else:  # 1y
            self.ax1_perf.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            self.ax1_perf.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))

        # Format de l’axe des X pour les dates
        self.perf_graph.autofmt_xdate(rotation=45)

        # --- REFRESH ---
        self.perf_graph.canvas.draw_idle()


    def clean_all_exercises(self):
        """
        Nettoie et prépare toutes les activités enregistrées :
        - formatage des dates
        - ajout de 'Date séance'
        - ajout du total des répétitions
        - ajout de l'état et des notes si absents
        - tri par date décroissante
        """

        for name, dict_exo in self.app.profile.all_exercise_dict.items():

            cleaned_dict_exo = []

            for record in dict_exo:
                # --- 1) Formatage de la date ---
                date_raw = record.get("Date")
                date_obj = None

                if isinstance(date_raw, datetime):
                    date_obj = date_raw

                elif isinstance(date_raw, str):
                    # On tente YYYY-MM-DD
                    try:
                        date_obj = datetime.strptime(date_raw, "%Y-%m-%d")
                    except Exception:
                        # On tente DD/MM/YYYY
                        try:
                            date_obj = datetime.strptime(date_raw, "%d/%m/%Y")
                        except Exception:
                            date_obj = None

                record["Date"] = date_obj

                # --- 2) Formatage affichage ---
                if date_obj is not None:
                    record["Date séance"] = date_obj.strftime("%d/%m/%Y")

                # --- 3) Total des répétitions ---
                series_keys = [
                    k for k in record.keys()
                    if k.startswith("S") and isinstance(record[k], (int, float))
                ]
                record["Total"] = sum(record[k] for k in series_keys)

                # --- 4) Etat ---
                if not record.get("Etat"):
                    record["Etat"] = SMILEY_DATA[5][0]

                # --- 5) Notes ---
                if not record.get("Notes"):
                    record["Notes"] = "..."

                cleaned_dict_exo.append(record)

            # --- 6) Tri par date décroissante ---
            cleaned_dict_exo.sort(
                key=lambda r: r.get("Date") or datetime.min,
                reverse=True
            )

            # --- 7) On replace dans la structure principale ---
            self.app.profile.all_exercise_dict[name] = cleaned_dict_exo

    def reorder_columns(self, dict_exo):
        """
        Réorganise les colonnes.
        """
        if not dict_exo:
            return dict_exo  # rien à faire si la liste est vide

        # Colonnes principales fixes
        colonnes = ["Date", "Date séance", "Kg"]

        # Colonnes dynamiques des séries (ex: S1, S2, ...)
        series_cols = sorted(
            [col for col in dict_exo[0].keys() if col.startswith("S")],
            key=lambda x: int(x[1:])
        )

        # Colonnes annexes (ex: Total_reps, Etat, Notes, etc.)
        colonnes_annexes = [
            col for col in dict_exo[-1].keys() if col not in colonnes + series_cols
        ]

        # Ordre final des colonnes
        ordre = colonnes + series_cols + colonnes_annexes

        # Réordonner chaque dict selon l'ordre défini
        reordered = [
            {col: row.get(col) for col in ordre}
            for row in dict_exo
        ]

        return reordered

    # def remove_volume_performance_graphs(self):
    #     """
    #     Retirer les graphiques de volume et de performance de l'UI.
    #     """

    #     self.ids.zone_2_view_content.opacity = 0
    #     self.ids.zone_2_view_content.disabled = True  # désactive les clics

    #     self.ids.zone_3_view_content.opacity = 0
    #     self.ids.zone_3_view_content.height = 0
    #     self.ids.zone_3_view_content.disabled = True  # désactive les clics


    # def add_volume_performance_graphs(self):
    #     """
    #     Ajouter les graphiques de volume et de performance de l'UI.
    #     """
    #     self.ids.zone_2_view_content.opacity = 1
    #     self.ids.zone_2_view_content.disabled = False  # active les clics

    #     self.ids.zone_3_view_content.opacity = 1
    #     self.ids.zone_3_view_content.height = self.ids.zone_3_view_content.minimum_height
    #     self.ids.zone_3_view_content.disabled = False  # active les clics

    def update_stats_resume(self, dict_exo):
        """
        MAJ des labels de l'encadré des résumés des activités
        :param dict_exo: dict des activités enregistrées de l'exo cible
        :return:
        """

        # Annuler MAJ si df_exo vide (exercice vient d'être ajouté)
        if len(dict_exo) ==0:
            return

        # Nombre d'activités totales
        self.ids.activity_total_value.text = str(len(dict_exo))

        # Nombre d'activités des 30 derniers jours
        limite = datetime.today() - timedelta(days=30)
        last_30_days = [row for row in dict_exo if row.get("Date") is not None and row["Date"] >= limite]
        self.ids.last_30_days_value.text = str(len(last_30_days))

        # Nombre d'activités de l'année en cours
        this_year = [row for row in dict_exo
                     if row.get("Date") is not None and row["Date"].year == self.app.today.year]

        self.ids.last_year_value.text = str(len(this_year))

    def create_exercise_settings(self, button):
        """
        Créer un menu déroulant des paramètres de l'exercice.
        :param button:
        :return:
        """

        menu_items = [
            {
                "text": "Renommer",
                "trailing_icon": "pencil",  # ajoute une icône à droite (à gauche = leading_icon)
                "on_release": lambda: (self.rename_exercise(), self.exercice_settings_menu.dismiss())
            },
            {
                "text": "Supprimer",
                "trailing_icon": "delete",
                "on_release": lambda: (self.confirm_delete_exercise(), self.exercice_settings_menu.dismiss())
            },
            {
                "text": "Nouveau",
                "trailing_icon": "plus-circle",
                "on_release": lambda: (self.open_add_exercise_dialog(), self.exercice_settings_menu.dismiss())
            },
        ]

        self.exercice_settings_menu = MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=2,
            radius=dp(10),  # arrondir les coins
            position = "bottom"
        )

        self.exercice_settings_menu.open()

    def rename_exercise(self):
        """
        Renomme l'exercice.
        """
        current_name = self.ids.exercise_menu_button.text
        self.rename_dialog = None

        def confirm_rename(*args):
            # Récuperer le nom de l'exercice saisi
            new_name = new_exercise_name.text.strip()  # .strip = supprime les espaces vides
            if not new_name:
                toast("Le nom ne peut pas être vide.")
                return
            if new_name == current_name:
                self.rename_dialog.dismiss()
                return
            if new_name in self.app.profile.all_exercise_dict:
                toast(f"Le nom '{new_name}' existe déjà.")
                return

            if current_name == "VIDE":
                toast(f"Aucun exercice n'a été ajouté")
                return

            # ✅ Récupérer les données et renommer la clé
            data = self.app.profile.all_exercise_dict.pop(current_name)  # data = liste de dicts
            self.app.profile.all_exercise_dict[new_name] = data

            # ✅ Met à jour l'affichage
            self.ids.exercise_menu_button.text = new_name
            self.app.record.update_exercise_content(new_name)

            # Fermer
            self.rename_dialog.dismiss()

        # Créer la zone pour le nv nom de l'exercice
        new_exercise_name = MDTextField(
            hint_text="Nouveau nom",
            text='',
            mode="rectangle"
        )

        # Créer le box de Dialog
        self.rename_dialog = MDDialog(
            title=f"Renommer l'exercice : {current_name}",
            type="custom",
            content_cls=new_exercise_name,
            buttons=[
                MDFlatButton(text="Annuler", on_release=lambda x: self.rename_dialog.dismiss()),
                MDRaisedButton(text="Valider", on_release=confirm_rename),
            ],
        )
        self.rename_dialog.open()

    def confirm_delete_exercise(self):
        """
        Ouvre une boîte de dialog pour confirmer la suppression de l'exercice.
        """
        current_name = self.ids.exercise_menu_button.text

        if current_name == "Ajoute un exercice":
            toast("Aucun exercice sélectionné")
            return

        if current_name == "Sélectionne un exercice":
            toast("Aucun exercice sélectionné")
            return

        # Boîte de confirmation
        self.delete_dialog = MDDialog(
            title="Confirmer la suppression",
            text=f"Es-tu sûr de vouloir supprimer l'exercice « {current_name} » ?",
            buttons=[
                MDFlatButton(
                    text="Annuler",
                    on_release=lambda x: self.delete_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Oui",
                    on_release=lambda x: self.delete_exercise(current_name),
                    md_bg_color = "red"
                ),
            ],
        )
        self.delete_dialog.open()

    def delete_exercise(self, name):
        """
        Supprimer l'exercice du dictionnaire.
        :param name: nom de l'exercise
        """
        self.delete_dialog.dismiss()

        # Supprimer l'exo du dictionnaire
        if name in self.app.profile.all_exercise_dict:
            del self.app.profile.all_exercise_dict[name]

        # Réinitialiser les boutons
        self.reset_exercise_menu_button()
        self.app.record.reset_exercise_menu_button()

        # Retirer les historiques
        self.remove_history_content()
        self.app.record.remove_history_content()

        # Retirer les widgets des graphs
        self.remove_volume_performance_graphs()

    def remove_history_content (self):
        """
        Retirer le bouton d'accès vers l'historique.
        :return:
        """

        # Retirer accès vers l'historique
        self.ids.history_content.height = 0
        self.ids.history_content.opacity = 0
        self.ids.history_content.disabled = True  # désactive les clics

    def add_history_content (self):
        """
        Ajouter le bouton d'accès vers l'historique
        :return:
        """
        # Ajouter accès vers l'historique
        self.ids.history_content.height = self.ids.history_content.minimum_height
        self.ids.history_content.opacity = 1
        self.ids.history_content.disabled = False  # active les clics

    def reset_exercise_menu_button (self):
        """
        Réinitialiser le texte du bouton d'exercice.
        """
        self.ids.exercise_menu_button.line_color = "red"
        if len(self.menu_name_exercise_item) <= 1:
            self.ids.exercise_menu_button.text = "Ajoute un exercice"
        else :
            self.ids.exercise_menu_button.text = "Sélectionne un exercice"


    def open_add_exercise_dialog(self):
        """
        Ouvre une boîte de dialog pour entrer le nom du nouvel exo.
        """
        # Zone d'entrée de texte pour le nouvel exercice
        new_exercise = MDTextField(
            hint_text="Nom du nouvel exercice",
            mode="rectangle"
        )

        # Box de Dialog pour ajouter l'exercice
        self.add_exercise_dialog = MDDialog(
            title="Ajouter un exercice",
            type="custom",
            content_cls=new_exercise,
            buttons=[
                MDFlatButton(
                    text="Annuler",
                    on_release=lambda x: self.add_exercise_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Ajouter",
                    on_release=lambda x: self.add_new_exercise(new_exercise.text)
                ),
            ],
        )

        # Ouvrir le dialog
        self.add_exercise_dialog.open()

    def add_new_exercise(self, new_name):
        """
        Ajouter le nouvel exercice dans le dict.
        """
        # Fermer le dialog
        self.add_exercise_dialog.dismiss()

        # Retirer les espaces vides du nouvel exo
        new_name = new_name.strip()

        # Ne rien faire si le champ est vide
        if not new_name:
            return

        # Ne rien faire si l'exercice existe déjà
        if new_name in self.app.profile.all_exercise_dict:
            toast(f"Le nom '{new_name}' existe déjà.")
            return

        # Associer un dict vide au nouvel exo
        self.app.profile.all_exercise_dict[new_name] = []

        # Mettre à jour le bouton avec le nouveau nom
        self.ids.exercise_menu_button.text = new_name

        # Mettre à jour l’affichage de l’historique
        self.select_exercise(new_name)
    
    def build_carousel_indicator(self):
        """
        Construit la rangée de points en fonction du nombre de slides.
        """

        self.carousel_indicator.clear_widgets()
        self.carousel_dots = []

        total = len(self.stats_carousel.slides)
        if total == 0:
            return

        for i in range(total):
            dot = MDIconButton(
                icon="checkbox-blank-circle",  # point “vide”
                icon_size=sp(8),
                theme_text_color="Custom",
                text_color=get_color_from_hex("#7D7D7D"),
                on_release=lambda btn, idx=i: self.stats_carousel.load_slide(self.stats_carousel.slides[idx])
            )
            self.carousel_dots.append(dot)
            self.carousel_indicator.add_widget(dot)

        # Appliquer l’état sélectionné au point courant
        self.update_carousel_indicator()

    def update_carousel_indicator(self, *args):
        """
        Met en évidence le point correspondant au slide courant.
        """
        if not self.carousel_dots:
            return

        current = self.stats_carousel.index
        for i, dot in enumerate(self.carousel_dots):
            if i == current:
                dot.icon = "checkbox-blank-circle"  # peut aussi être "circle"
                dot.icon_size = sp(12)  # un peu plus grand
                dot.text_color = self.theme_cls.primary_color
            else:
                dot.icon = "checkbox-blank-circle-outline"
                dot.icon_size = sp(8)
                dot.text_color = get_color_from_hex("#7D7D7D")

    # def update_graph_volume(self, dict_exo):
    #     """
    #     MAJ du graphique du volume.
    #     """

    #     # Annuler MAJ si df_exo vide (exercice vient d'être ajouté)
    #     if len(dict_exo) == 0:
    #         return

    #     # --- Paramétrage du dataframe ---
    #     month = self.app.today.month + 1
    #     year = self.app.today.year - 1
    #     if month == 13:
    #         month = 1
    #         year += 1
    #     self.start = datetime(year, month, 1)

    #     # Dataframe de l'année dernière
    #     last_year_activities = [row for row in dict_exo
    #                             if row.get("Date") is not None and row["Date"] >= self.start]

    #     # Compter le nombre de séances par mois (format AAAA-MM)
    #     activity_counter = Counter()
    #     for row in last_year_activities:
    #         month_str = row["Date"].strftime("%Y-%m")
    #         activity_counter[month_str] += 1

    #     # Générer la liste de tous les mois complets
    #     months_full = []
    #     current = self.start
    #     while current <= self.app.today:
    #         months_full.append(current.strftime("%Y-%m"))
    #         current += relativedelta(months=1)

    #     # Créer la liste finale avec tous les mois (0 si pas d'activité)
    #     activity_by_month_full = [{"mois": m, "nb_seances": activity_counter.get(m, 0)}
    #                               for m in months_full]

    #     # MAJ de la moyenne mensuelle sur la dernière année (Encadré 2 : Statistiques)
    #     moy = sum(d["nb_seances"] for d in activity_by_month_full) / len(activity_by_month_full)
    #     self.ids.freq_month_moy_value.text = str(round(moy, 2))

    #     # ✅ Conversion en datetime
    #     for d in activity_by_month_full:
    #         d["mois_dt"] = datetime.strptime(d["mois"], "%Y-%m")


    #     # --- Paramétrages du graphique matplotlib ---
    #     # Nettoyer les axes
    #     self.volume_ax.clear()

    #     # Extraire les données du dict pour matplotlib
    #     x_dates = [d["mois_dt"] for d in activity_by_month_full]
    #     y_counts = [d["nb_seances"] for d in activity_by_month_full]

    #     # ✅ Personnalisation des barres
    #     self.volume_ax.bar(x_dates, y_counts, width=20, color="lightgreen")

    #     # Mise en forme
    #     self.volume_ax.set_ylabel("Nombre d'activités", color="lightgreen")
    #     self.volume_ax.tick_params(axis="y", labelcolor="lightgreen")
    #     self.volume_ax.set_title("Evolution mensuelle des activités (1 an)",
    #                              color="white")

    #     # Axe X avec chaque mois
    #     self.volume_ax.xaxis.set_major_locator(mdates.MonthLocator())  # un tick par mois
    #     self.volume_ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    #     self.volume_graph.autofmt_xdate()

    #     # Limitation des axes du graphique
    #     self.volume_ax.set_ylim(0, max(y_counts) + 1)

    #     # Redessiner matplotlib
    #     self.volume_graph.canvas.draw_idle()

    # def update_graph_perf(self, dict_exo):
    #     """
    #     MAJ du graph perfs.
    #     """

    #     # Annuler MAJ si nouvel exercice
    #     if len(dict_exo) == 0:
    #         return

    #     self.ax1_perf.clear()

    #     # Supprime complètement l'axe 2
    #     self.ax2_perf.remove()

    #     # Recréer l'axe 2
    #     self.ax2_perf = self.ax1_perf.twinx()

    #     # Préparer les données
    #     dates = [r["Date"] for r in dict_exo if r.get("Date") is not None]
    #     kgs = [r.get("Kg", 0) for r in dict_exo if r.get("Date") is not None]
    #     total_reps = [r.get("Total", 0) for r in dict_exo if r.get("Date") is not None]

    #     # Axe gauche -> Poids soulevé
    #     self.ax1_perf.plot(dates, kgs, marker="o", color="skyblue", label="Poids (Kg)")
    #     self.ax1_perf.fill_between(dates, kgs, color="skyblue", alpha=0.2)
    #     self.ax1_perf.set_ylabel("Poids (Kg)", color="skyblue")
    #     self.ax1_perf.tick_params(axis="y", labelcolor="skyblue")

    #     # Axe droit -> Total répétitions
    #     self.ax2_perf.plot(dates, total_reps, marker="s", color="orange", label="Total répétitions")
    #     self.ax2_perf.fill_between(dates, total_reps, color="orange", alpha=0.2)
    #     self.ax2_perf.set_ylabel("Total répétitions", color="orange")
    #     self.ax2_perf.tick_params(axis="y", labelcolor="orange")

    #     # Format de l’axe des X pour les dates : un tick tous les 2 mois
    #     self.ax1_perf.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    #     self.ax1_perf.xaxis.set_major_formatter(mdates.DateFormatter("%b%y"))
    #     self.perf_graph.autofmt_xdate(rotation=45)

    #     # Limitation de l'axe x (période d'1 an)
    #     self.ax1_perf.set_xlim(self.start, self.app.today)

    #     # Redessiner matplotlib
    #     self.perf_graph.canvas.draw_idle()
