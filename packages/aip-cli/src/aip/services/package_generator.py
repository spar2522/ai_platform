from pathlib import Path
from string import Template


class PackageGenerator:
    """Generates the skeleton for a new AI Platform package."""

    TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "package"

    def create_package(
        self,
        package_name: str,
    ) -> None:

        root = Path("packages") / package_name

        if root.exists():
            raise ValueError(f"Package '{package_name}' already exists.")

        module_name = package_name.replace("-", "_")

        class_name = "".join(word.capitalize() for word in module_name.split("_"))

        directories = [
            root,
            root / "src" / module_name,
            root / "tests",
            root / "examples",
        ]

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._copy_template(
            "README.md.template",
            root / "README.md",
            package_name,
            module_name,
            class_name,
        )

        self._copy_template(
            "pyproject.toml.template",
            root / "pyproject.toml",
            package_name,
            module_name,
            class_name,
        )

        (root / "src" / module_name / "__init__.py").touch()

        self._copy_template(
            "module.py.template",
            root / "src" / module_name / f"{module_name}.py",
            package_name,
            module_name,
            class_name,
        )

        self._copy_template(
            "test.py.template",
            root / "tests" / f"test_{module_name}.py",
            package_name,
            module_name,
            class_name,
        )

        print(f"✅ Created package '{package_name}'")

    def _copy_template(
        self,
        template_name: str,
        destination: Path,
        package_name: str,
        module_name: str,
        class_name: str,
    ) -> None:

        template_text = (self.TEMPLATE_DIR / template_name).read_text(
            encoding="utf-8",
        )

        template = Template(template_text)

        output = template.safe_substitute(
            PACKAGE_NAME=package_name,
            MODULE_NAME=module_name,
            CLASS_NAME=class_name,
        )

        destination.write_text(
            output,
            encoding="utf-8",
        )
