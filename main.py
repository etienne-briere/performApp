import asyncio
import logging

from kivy.logger import Logger
from app.app import PerformApp
from utils.logger import setup_logger

async def main(app):
    """Point d'entrée asynchrone de l'application"""
    # Lancement de l'application en mode asynchrone
    await app.async_run("asyncio")

if __name__ == '__main__':
    # Configuration du logging
    setup_logger()
    Logger.setLevel(logging.DEBUG)

    # Lancement de l'application
    app = PerformApp()
    asyncio.run(main(app))

