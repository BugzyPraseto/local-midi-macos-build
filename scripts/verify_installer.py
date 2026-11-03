"""Check the package architecture, successful build checks and SHA-256."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(directory, architecture):
    reports = list(directory.glob("Local MIDI-*-macOS-" + architecture + "-unsigned.pkg.json"))
    if len(reports) != 1:
        raise ValueError("Expected exactly one " + architecture + " installer report")
    report_path = reports[0]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("architecture") != architecture:
        raise ValueError("The engine architecture does not match the requested package")
    if report.get("runtime", {}).get("architecture") != architecture:
        raise ValueError("The bundled Python architecture does not match the package")
    if set(report.get("native_wrapper_architectures", [])) != {"arm64", "x86_64"}:
        raise ValueError("The native app and VST3 are not reported as universal2")
    for check in ("native_tests", "relocated_runtime_self_test"):
        if report.get(check) != "passed":
            raise ValueError("Build check did not pass: " + check)
    package_name = report_path.name.removesuffix(".json")
    if report.get("package") != package_name:
        raise ValueError("The package filename does not match its report")
    package = directory / package_name
    size = package.stat().st_size
    if not 0 < size < 2 * 1024**3:
        raise ValueError("The installer must be nonempty and below the 2 GiB release asset limit")
    checksum = hashlib.sha256()
    with package.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    if checksum.hexdigest() != report.get("sha256"):
        raise ValueError("The package checksum does not match its build report")
    print("Verified " + package_name)
    print("Engine: " + architecture + "; app/VST3: universal2; build checks: passed")
    print("SHA-256: " + checksum.hexdigest())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--arch", choices=("arm64", "x86_64"), default="arm64")
    arguments = parser.parse_args()
    try:
        verify(arguments.directory, arguments.arch)
    except (ValueError, OSError) as error:
        parser.exit(1, "Installer verification failed: " + str(error) + "\n")
