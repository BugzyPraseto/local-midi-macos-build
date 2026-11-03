"""Apply verified packaging corrections to the extracted, checksum-pinned kit."""
import argparse
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET


def prepare(root):
    script = root / "native/macos/build_installer.py"
    source = script.read_text(encoding="utf-8")
    old = "MINIMUM_MACOS = (12, 0)"
    new = "MINIMUM_MACOS = (12, 3)"
    if source.count(old) == 1:
        script.write_text(source.replace(old, new, 1), encoding="utf-8")
    elif source.count(new) != 1:
        raise ValueError("The build kit's minimum-macOS setting has changed; review it before patching")

    welcome = root / "native/macos/resources/Welcome.html"
    text = welcome.read_text(encoding="utf-8")
    welcome.write_text(text.replace("macOS 12 or later", "macOS 12.3 or later"), encoding="utf-8")

    # Confirm the same minimum reaches all packaging decisions. Keep the
    # Mach-O checks active: dependencies requiring a later OS must still fail.
    spec = importlib.util.spec_from_file_location("prepared_mac_packaging", script)
    packaging = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(packaging)
    assert packaging.minimum_macos() == "12.3"
    commands = "cmd LC_BUILD_VERSION\ncmdsize 32\nplatform 1\nminos 12.3\n"
    packaging.validate_macos_load_commands(commands, "SciPy macOS 12.3 regression fixture")
    for newer in ("12.4", "13.0"):
        try:
            packaging.validate_macos_load_commands(commands.replace("12.3", newer), "fixture")
        except ValueError:
            pass
        else:
            raise ValueError("The runtime audit accepted a dependency newer than the installer minimum")

    captured = []
    original_run = packaging.run
    try:
        packaging.run = lambda arguments, **kwargs: captured.append([str(x) for x in arguments]) or SimpleNamespace(stdout="")
        packaging.native_build(root, root / "build/prepare-check", 2)
    finally:
        packaging.run = original_run
    assert "-DCMAKE_OSX_DEPLOYMENT_TARGET=12.3" in captured[0]
    for architecture in packaging.ARCHITECTURES:
        assert packaging.installation_plan("0.2.0", architecture)["minimum_macos"] == "12.3"
        distribution = ET.fromstring(packaging.distribution_xml("0.2.0", "fixture.pkg", architecture))
        assert distribution.find("volume-check/allowed-os-versions/os-version").attrib["min"] == "12.3"
        environment = packaging.build_environment(root / "build/prepare-check", root / "Engine", architecture)
        assert environment["MACOSX_DEPLOYMENT_TARGET"] == "12.3"
        options = packaging.compatible_wheel_options(architecture)
        assert options[options.index("--platform") + 1] == "macosx_12_3_" + architecture
    assert packaging.validate_host("Darwin", "x86_64", "12.6.2") == "x86_64"
    print("Prepared build kit: macOS 12.3 minimum; installer/native/runtime settings agree.")
    print("Regression checks passed: SciPy 12.3 is accepted; newer deployment targets are rejected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    arguments = parser.parse_args()
    try:
        prepare(arguments.root.resolve())
    except (OSError, ValueError, AssertionError) as error:
        parser.exit(1, "Build-kit preparation failed: " + str(error) + "\n")
