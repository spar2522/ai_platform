import typer
from aip.commands.create import create_app

app = typer.Typer()

app.add_typer(
    create_app,
    name="create",
)

if __name__ == "__main__":
    app()
