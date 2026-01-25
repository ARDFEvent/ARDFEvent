<div align="center">
  <img src="icons/icon.png" alt="Logo" height="200px">
  <h1>JJ ARDFEvent</h1>

  <p>
    <a href="README.md">Česky</a> | <b>English</b>
  </p>

  <p>
    <img src="https://img.shields.io/github/v/tag/ARDFEvent/ARDFEvent" alt="GitHub Release">
    <img src="https://img.shields.io/github/license/ARDFEvent/ARDFEvent" alt="GitHub License">
    <img src="https://wakapi.dev/api/badge/jacobcz/interval:30_days/project:ARDFEvent?label=last%2030%20days" alt="Wakapi Time">
  </p>

  <p>
    <b>Open-source software for processing results in ARDF.</b><br>
    Designed to be as simple as possible and to make the work of the IT team easier. :sparkles:
  </p>

  <p>
    Code author: Jakub Jiroutek :man_technologist:, logo author: Dan Zeman :art:
  </p>
</div>

This software is intended to be used on a computer/laptop with a mouse and keyboard. If you want software only for
Android, use [kolskypavel/Radio-O-Manager](https://github.com/kolskypavel/Radio-O-Manager)

## Program Features :toolbox:

1.  [x] Data management (competitors, categories, controls)
2.  [x] SI chip readout (all versions)
3.  [x] Ticket printing on ESC-POS compatible printers (ticket for competitor and for string)
4.  [x] 100% integration with ROBis (via open plugin)
5.  [x] Export results to various formats (CSV, HTML, IOF XML, ARDF JSON)
6.  [x] Import competitors and categories from CSV
7.  [x] Tracking competitors in the forest and their time limit expiration
8.  [x] Multi-stage races (via open plugin)
9.  [x] Web server for competitors at the finish line (in case of no mobile data at the finish)
10. [x] Start numbers
11. [x] Start list (including preventing consecutive starts of competitors from the same club in the same category)
12. [x] Integration with OChecklist
13. [x] Merging controls
14. [x] Multiplatform (Linux, Windows, macOS)
15. [x] Localization (Czech, English)
16. [x] Plugin system for feature extension

## Installation :wrench:

### Standard build

First, download the latest version of the program [from here](https://github.com/ARDFEvent/ARDFEvent/releases).
Select the package for your operating system. Then proceed according to the instructions below.

I only build packages for:

- Windows 10 and newer (x64)
- Linux (x64)

For others, see the Advanced chapter.

#### Windows

An installer is available for Windows.

1. Download the `ARDFEvent-<version>-winx64.exe` file.
2. Run the installer and follow the on-screen instructions.
3. After the installation is complete, launch the program from the Start menu or desktop.

#### Linux :penguin:

For Linux, a gzipped tarball file containing the pre-compiled application is available.

1. Download the `ARDFEvent-<version>-anylinuxx64.tar.gz` file.
2. Unpack the zip file into your chosen directory.
3. Open a terminal and navigate to the unpacked directory.
4. Run the program with the command:

```shell
./ARDFEvent
```

### Advanced

If your operating system is not among those listed above (it should essentially run on anything that supports Qt and the
Rust toolchain, it does not run on Android or iOS), or if you want to customize the program yourself, follow these
steps:

For a custom build, you need:

- Python 3.12 or newer :snake:
- Rust toolchain (rustc 1.92.0 or newer) :crab:
- git

1. Make sure you have all the requirements for a custom build (see above).
2. Clone the repository from GitHub:

```shell
git clone https://github.com/ARDFEvent/ARDFEvent.git
```

3. Navigate to the project directory:

```shell
cd ARDFEvent
```

4. Run the script to build the binary components.

```shell
# Linux / macOS (bash/zsh)
bash build.sh

# Windows (CMD)
build.bat
```

5. Activate the virtual environment:

```shell
# Linux / macOS
source .venv/bin/activate

# Windows (CMD)
.\.venv\Scripts\activate
```

6. Run the program with the command:

```shell
python src/main.py
```

## Support :handshake:

Please report all bugs via [GitHub Issues](https://github.com/ARDFEvent/ARDFEvent/issues).
If you have an idea for a new feature, you can also add it there as a suggestion.

Please also report urgent issues on Issues; I will receive an email notification.

## Documentation :book:

Documentation is available [here](https://github.com/ARDFEvent/ARDFEvent/wiki) (GitHub wiki) - for now only in czech, it
will be translated in the near future.

## Testing :test_tube:

To run the tests, you need to have `pytest` and `pytest-qt` installed (both are in `requirements.txt`). Then run the
command:

```shell
pytest -q
```
