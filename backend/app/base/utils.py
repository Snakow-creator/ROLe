from levels.load import load_levels

import logging


async def load_data():
    """"load const data"""

    await load_levels()
    logging.info("load Levels")
