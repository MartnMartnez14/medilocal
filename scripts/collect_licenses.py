"""Build-time only: retain runtime license texts in downloadable packages."""
import platform
import shutil
import sys
import tkinter as tk
import urllib.request
from pathlib import Path


def main():
    bundle = Path(sys.argv[1])
    output = bundle / "licenses"
    output.mkdir(exist_ok=True)
    sources = {
        "Python.txt": f"https://raw.githubusercontent.com/python/cpython/v{platform.python_version()}/LICENSE",
    }
    root = tk.Tk()
    root.withdraw()
    try:
        for component, version in (("tcl", root.tk.call("info", "patchlevel")), ("tk", root.tk.call("package", "provide", "Tk"))):
            tag = "core-" + version.replace(".", "-")
            sources[f"{component}-{version}.txt"] = f"https://raw.githubusercontent.com/tcltk/{component}/{tag}/license.terms"
    finally:
        root.destroy()
    for filename, url in sources.items():
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read()
        if len(content) < 500:
            raise RuntimeError("Incomplete runtime license")
        (output / filename).write_bytes(content)
    # Linux binary dependency copyright notices from the exact build distribution.
    if sys.platform == "linux":
        for name in ("libtcl8.6", "libtk8.6", "libsqlite3-0", "zlib1g", "libbz2-1.0", "liblzma5", "libffi8", "libexpat1", "libssl3", "libuuid1"):
            source = Path("/usr/share/doc") / name / "copyright"
            if source.is_file():
                shutil.copyfile(source, output / f"{name}-copyright.txt")
    # Windows Python distributions also supply additional library notices here.
    runtime = Path(sys.base_prefix) / "LICENSE.txt"
    if runtime.is_file():
        shutil.copyfile(runtime, output / "Python-runtime-LICENSE.txt")
    (output / "SOURCES.txt").write_text("\n".join(f"{name}: {url}" for name, url in sources.items()) + "\n", encoding="utf-8")
    print("Runtime license texts included.")


if __name__ == "__main__":
    main()
