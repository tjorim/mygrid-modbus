"""Check the wheel/sdist boundary before a library release."""

from email.parser import BytesParser
from pathlib import Path
import tarfile
import tomllib
import zipfile

from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Ensure artifacts carry typing and only the independent protocol package."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    (wheel_path,) = (ROOT / "dist").glob("mygrid_modbus-*-py3-none-any.whl")
    version = wheel_path.name.split("-")[1]  # hatch-vcs derives it from the git tag
    with zipfile.ZipFile(wheel_path) as wheel:
        names = wheel.namelist()
        assert "mygrid_modbus/py.typed" in names
        assert "mygrid_modbus/__init__.py" in names
        assert "mygrid_modbus/device.py" in names
        assert "mygrid_modbus/battery.py" in names
        assert all(name.startswith(("mygrid_modbus/", f"mygrid_modbus-{version}.dist-info/")) for name in names)
        metadata = BytesParser().parsebytes(wheel.read(f"mygrid_modbus-{version}.dist-info/METADATA"))
        assert metadata["Name"] == project["name"]
        assert metadata["Version"] == version
        assert metadata["Requires-Python"] == ">=3.12"
        requirements = [Requirement(value) for value in metadata.get_all("Requires-Dist", [])]
        assert {requirement.name for requirement in requirements} == {"modbus-connection"}
        declared_dependencies = [
            *project["dependencies"],
            *(dependency for dependencies in project["optional-dependencies"].values() for dependency in dependencies),
        ]
        assert {requirement.specifier for requirement in requirements} == {
            Requirement(dependency).specifier for dependency in declared_dependencies
        }
        assert sum(requirement.marker is None for requirement in requirements) == 1
        assert set(metadata.get_all("Provides-Extra", [])) == {"tmodbus", "pymodbus"}
        assert {extra for requirement in requirements for extra in requirement.extras} == {"tmodbus", "pymodbus"}
    with tarfile.open(ROOT / "dist" / f"mygrid_modbus-{version}.tar.gz") as sdist:
        names = sdist.getnames()
        assert any(name.endswith("/src/mygrid_modbus/py.typed") for name in names)
        assert not any("custom_components/" in name for name in names)
    print("Wheel and sdist contain the independent typed library and expected metadata.")


if __name__ == "__main__":
    main()
