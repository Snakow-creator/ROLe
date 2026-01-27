from levels.load import load_levels
from baseTasks.load import load_baseTasks

import logging


async def load_data():
    """"load const data"""
    await load_baseTasks()
    logging.info("load BaseTasks")

    await load_levels()
    logging.info("load Levels")
