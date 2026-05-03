from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import StringProperty
from kivymd.uix.pickers import MDDatePicker


class SetRow(MDBoxLayout):
    pass


class EditSessionDialogContent(MDBoxLayout):
    date = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_rows = []

    def open_date_picker(self):
        picker = MDDatePicker()
        picker.bind(on_save=self.on_date_selected)
        picker.open()

    def on_date_selected(self, instance, value, date_range):
        self.date = str(value)
        self.ids.date_btn.text = self.date

    def add_set(self, weight="", reps=""):
        row = SetRow()
        row.ids.weight.text = str(weight)
        row.ids.reps.text = str(reps)

        self.ids.sets_container.add_widget(row)
        self.set_rows.append(row)

    def get_data(self):
        sets = []
        for row in self.set_rows:
            try:
                w = float(row.ids.weight.text)
                r = int(row.ids.reps.text)
                sets.append({"w": w, "r": r})
            except:
                pass

        return {
            "date": self.date,
            "rpe": self.ids.rpe_field.text,
            "notes": self.ids.notes_field.text,
            "sets": sets
        }