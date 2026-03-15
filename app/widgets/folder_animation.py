import os
from kivy.uix.image import Image
from kivy.clock import Clock

class FolderAnimation(Image):
    ''' Affiche une animation image par image depuis un dossier. '''
    def __init__(self, image_folder='images', interval=0.2, loop=True, **kwargs):
        super().__init__(**kwargs)
        self.interval = interval
        self.loop = loop
        self.frame_index = 0
        self.anim = None

    def on_kv_post(self, base_widget):
        """Appelé automatiquement quand les propriétés du KV sont appliquées."""
        self.set_gif(self.image_folder, self.interval, self.loop)

    def set_gif(self, image_folder, interval=0.2, loop=True):
        ''' Change le dossier d’animation en direct. '''
        if self.anim:
            self.anim.cancel()

        self.loop = loop  # met à jour la valeur
        all_files = os.listdir(image_folder)
        image_files = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        self.frames = sorted([os.path.join(image_folder, f) for f in image_files])

        if not self.frames:
            raise Exception(f"Aucune image trouvée dans {image_folder}")

        self.frame_index = 0
        self.source = self.frames[0]

        self.anim = Clock.schedule_interval(self.next_frame, interval)

    def next_frame(self, dt):
        if self.loop:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.source = self.frames[self.frame_index]
        else:
            if self.frame_index < len(self.frames) - 1:
                self.frame_index += 1
                self.source = self.frames[self.frame_index]
            else:
                # On est à la dernière frame, on stoppe
                if self.anim:
                    self.anim.cancel()
                    self.anim = None

    def restart_animation(self):
        """Force le redémarrage depuis la frame 0."""
        if self.anim:
            self.anim.cancel()  # stoppe l’ancienne animation

        self.frame_index = 0
        if hasattr(self, "frames") and self.frames:
            self.source = self.frames[0]  # affiche la première image

        self.opacity = 1  # rendre visible au restart
        # relance la boucle d’animation
        self.anim = Clock.schedule_interval(self.next_frame, self.interval)

    def restart_animation2(self):
        """
        Redémarre l'animation depuis la 1ère frame
        et la fait disparaître automatiquement à la fin.
        """
        # Annuler une animation existante
        if self.anim:
            self.anim.cancel()

        # Repartir du début
        self.frame_index = 0
        if self.frames:
            self.source = self.frames[0]

        self.opacity = 1  # visible au démarrage

        # Lancer l'animation avec un callback spécial
        self.anim = Clock.schedule_interval(self._next_frame_disappear, self.interval)

    def _next_frame_disappear(self, dt):
        """Version spéciale : joue l'animation et disparaît à la fin."""
        # Si pas encore à la dernière frame → avancer
        if self.frame_index < len(self.frames) - 1:
            self.frame_index += 1
            self.source = self.frames[self.frame_index]
            return

        # Sinon → dernière frame atteinte
        if self.anim:
            self.anim.cancel()
            self.anim = None

        # Disparaît automatiquement
        self.opacity = 0

