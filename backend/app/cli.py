from models.settings import baseSettings, settings
from backend.app.base.database import init_db

from levels.load import load_levels
from items.load import load_items

import asyncclick as click

__all__ = []


@click.group()
async def cli():
    settings.collection_name = baseSettings.collection_name
    await init_db() # инициализируем коллекцию



@cli.command(name="load_data")
async def load_data():
    """"load const data"""
    click.echo("load_data")
    await load_levels()
    click.echo("Levels loaded")
    await load_items()
    click.echo("Items loaded")


if __name__ == "__main__":
    cli(_anyio_backend="asyncio")
