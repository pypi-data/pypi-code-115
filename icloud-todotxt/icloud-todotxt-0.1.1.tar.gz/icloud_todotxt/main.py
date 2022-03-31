"""Synchronize your local 'todo.txt' with iCloud."""

import os
from pathlib import Path
from shutil import copyfile, copyfileobj
import typer
from pyicloud import PyiCloudService


APPLE_ID = os.getenv("APPLE_ID")
if APPLE_ID is None:
    typer.echo("Environment variable `APPLE_ID` must be set!")
    raise typer.Exit(code=1)

TODO_FILE = Path(os.getenv("TODO_FILE"))
if TODO_FILE is None:
    typer.echo("Environment variable `TODO_FILE` must be set!")
    raise typer.Exit(code=1)

app = typer.Typer()
api = PyiCloudService(APPLE_ID)

# Fix for https://github.com/picklepete/pyicloud/issues/326.
api.drive.params["clientId"] = api.client_id


@app.command()
def download():
    """Download the 'todo.txt' from iCloud."""
    try:
        todotxt = api.drive["ToDo"]["todo.txt"]
    except KeyError as error:
        typer.echo("Could not find `todo.txt` in iCloud.")
        raise typer.Exit(code=1) from error

    with todotxt.open(stream=True) as response:
        with open(TODO_FILE, "wb") as file_out:
            copyfileobj(response.raw, file_out)


@app.command()
def upload():
    """Upload the `todo.txt` to iCloud."""
    # Delete the old `todo.txt`, otherwise the new file is called `todo 2.txt`.
    try:
        todotxt = api.drive["ToDo"]["todo.txt"]
        todotxt.delete()
    except KeyError:
        pass

    copyfile(TODO_FILE, "todo.txt")
    with open("todo.txt", "rb") as file_in:
        api.drive["ToDo"].upload(file_in)
    os.remove("todo.txt")
