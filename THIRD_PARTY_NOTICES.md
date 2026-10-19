# Third-party components

MediLocal source code is MIT licensed. It uses Python's standard library only;
there are no application pip dependencies, online fonts, analytics or network APIs.
Packaged distributions include their own Python/Tcl/Tk runtime and relevant
license texts in `licenses/`, collected during the build for the runtime versions
actually used. These components retain their own licenses:

- Python: [PSF License Agreement and history](https://docs.python.org/3/license.html).
- Tcl/Tk: [Tcl/Tk license terms](https://www.tcl-lang.org/software/tcltk/license.html), permissive BSD-style licenses.
- SQLite: [public domain dedication](https://www.sqlite.org/copyright.html).
- PyInstaller bootloader: [GPL with an exception permitting distribution of bundled applications under their own license](https://pyinstaller.org/en/stable/license.html).

PyInstaller is a build tool, not an application dependency. Pillow is used only by
the optional maintainer screenshot script and is not imported or bundled by the app.
Keep the `_internal` directory and all runtime license files in downloadable packages.
