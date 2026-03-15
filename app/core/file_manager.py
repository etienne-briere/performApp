from kivymd.uix.filemanager import MDFileManager

class FileManagerController:
    def __init__(self, app):
        self.app = app
        self.manager = MDFileManager(
            exit_manager=self.close,
            select_path=self.select,
            preview=False,
            ext=[".xls", ".xlsx"]
        )

    def open(self):
        self.manager.show(".")

    def select(self, path):
        print("Selected:", path)
        self.close()

    def close(self, *args):
        self.manager.close()
