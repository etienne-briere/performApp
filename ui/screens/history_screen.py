import asyncio
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty, ObjectProperty

from kivymd.uix.datatables import MDDataTable
from kivymd.uix.screen import MDScreen

from kivymd.toast import toast

from config import ROW_HISTORY_COUNT, FONT_SIZE_BUTTON, FONT_SIZE_BUTTON2, FONT_STYLE_SUBTITLE1, FONT_STYLE_SUBTITLE2, ICON_SIZE

import threading


class HistoryScreen(MDScreen):

    # Properties pour l'UI
    font_size_button = NumericProperty(FONT_SIZE_BUTTON) # taille du texte des boutons
    font_size_button2 = NumericProperty(FONT_SIZE_BUTTON2) # taille du texte des boutons secondaires
    font_style_subtitle1 = StringProperty(FONT_STYLE_SUBTITLE1) # style du texte des sous-titres
    font_style_subtitle2 = StringProperty(FONT_STYLE_SUBTITLE2) # style du texte des titres des encadrés
    icon_size = NumericProperty(ICON_SIZE) # taille des icônes

    def __init__(self, app=None, **kwargs):
        super().__init__(**kwargs)

        self.app = app
        self.checked_rows = []
        self.origin_screen_name = None

    def on_pre_enter(self):
        """
        Exécuter juste avant que l'écran devienne visible
        """
        # Recup des variables
        self.dict_exo = self.app.view.dict_exo
        self.exercise_name = self.app.view.selected_exercise_name

        # Modif titre
        self.ids.top_bar.title = f"Historique : {self.exercise_name}"

        

    def on_enter(self, *args):
        """ Appelé lorsque on entre dans l'écran. """
        # Gif de chargement activé
        self.ids.loader_gif.opacity = 1

        # Lancer le thread de construction des données
        threading.Thread(target=self._prepare_table_data, daemon=True).start()

    # ---------------------------------------------------
    #           THREAD → Prépare les données
    # ---------------------------------------------------
    def _prepare_table_data(self):
        """Cette fonction tourne EN DEHORS du thread UI."""
        print("check 1")
        #  ️Récupération des colonnes à partir du premier élément
        columns_list = list(self.dict_exo[0].keys())

        # Supprimer la première colonne
        columns_list = columns_list[1:]

        # Préparation des colonnes pour MDDataTable
        columns = []
        for col in columns_list:
            if col == "Etat":
                col_width = dp(20)
            else:
                # longueur max = max(longueur du nom de colonne, des valeurs de la colonne)
                max_len = max(
                    [len(str(col))] +
                    [len(str(row.get(col, ""))) for row in self.dict_exo]
                )
                # 🔹 multiplier par un facteur pour convertir en dp (ajustable)
                col_width = dp(max_len * 3.5)

            columns.append((col, col_width))

        # Préparer les lignes
        rows = []
        for row_dict in self.dict_exo:
            # On récupère uniquement les colonnes dans l'ordre choisi
            row = [str(row_dict.get(col, "")) for col in columns_list]

            # Gestion spéciale de l'icône "Etat"
            if "Etat" in columns_list:
                idx = columns_list.index("Etat")
                icon_name = row[idx]
                color = self.app.record.get_smiley_color(icon_name)
                row[idx] = (icon_name, color, "")

            rows.append(tuple(row))

        # Une fois fini → ui thread
        Clock.schedule_once(lambda dt: self._create_table(columns, rows))

    # ---------------------------------------------------
    #           UI THREAD → création du MDDataTable
    # ---------------------------------------------------
    def _create_table(self, columns, rows):
        """Appelé sur le thread principal."""

        # Construire le tableau proprement
        table = MDDataTable(
            size_hint=(1, 0.8),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            use_pagination=True,
            rows_num=ROW_HISTORY_COUNT,
            column_data=columns,
            row_data=rows,
            check=True
        )

        table.bind(on_check_press=self.on_check_press)

        # Afficher la table
        self.ids.table_container.add_widget(table)

        # Cacher loader
        self.ids.loader_gif.opacity = 0

    def open_history(self, instance):
        """
        Passe à l'écran de l'historique et affiche le DataFrame complet.
        """

        if self.app.view.dict_exo:
            # Changement de l'écran
            self.app.sm.current = "history"

        else :
            toast("Aucune activité enregistrée")

        # Trouver l'écran parent du bouton
        origin_screen = self.get_parent_screen(instance)
        if origin_screen:
            self.origin_screen_name = origin_screen.name
            print("➡ Écran d’origine :", self.origin_screen_name)


    def get_parent_screen(self, widget):
        while widget:
            if widget.__class__.__name__.endswith("Screen"):
                return widget
            widget = widget.parent
        return None

    def on_check_press(self, instance_table, current_row):
        """Ajoute ou enlève une ligne des cases cochées"""
        if current_row in self.checked_rows:
            self.checked_rows.remove(current_row)
        else:
            self.checked_rows.append(current_row)


    def delete_checked_rows(self, *args):
        """Supprime les lignes cochées dans self.dict_exo et reconstruit le tableau"""

        print(f"lignes cochées : {self.checked_rows}")
        if not self.checked_rows:
            return

        # ✅ Convertir les lignes cochées en listes de valeurs (les 6 premières seulement)
        to_remove = [list(row)[:6] for row in self.checked_rows]

        # ✅ Garder uniquement les lignes qui NE correspondent PAS aux lignes cochées
        new_dict_exo = []
        for row_dict in self.dict_exo:
            row_values = list(map(str, row_dict.values()))[1:7]
            if row_values not in to_remove:
                new_dict_exo.append(row_dict)

        # ✅ Mettre à jour les données de l'exercice courant
        self.dict_exo = new_dict_exo
        self.app.profile.all_exercise_dict[self.exercise_name] = self.dict_exo

        # ✅ Réinitialiser la sélection
        self.checked_rows.clear()

        # ✅ Retirer la table actuelle
        self.ids.table_container.clear_widgets()

        # ✅ Réinitialiser la table dans un thread
        threading.Thread(target=self._prepare_table_data, daemon=True).start()

        # Gif de chargement activé
        self.ids.loader_gif.opacity = 1

    def on_pre_leave(self, *args):
        # Recharger les données
        self.app.view.select_exercise(self.exercise_name)

    def on_leave(self, *args):
        # Retirer le tableau
        self.ids.table_container.clear_widgets()

    def go_back(self, *args):
        self.app.root.ids.screen_manager.current = self.origin_screen_name
