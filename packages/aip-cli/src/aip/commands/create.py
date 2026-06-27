import typer

from aip.services.package_generator import PackageGenerator

create_app = typer.Typer()


@create_app.command()
def package(
    package_name: str,
):
    """
    Create a new AI Platform package.
    """

    PackageGenerator().create_package(package_name)
