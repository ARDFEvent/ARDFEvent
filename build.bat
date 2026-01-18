@echo off
setlocal

echo Cleanup...
del /F /Q "src\ui\resources.py" 2>nul
del /F /Q "src\ui\resources_init.py" 2>nul

echo Create and activate venv...

if not exist ".venv\Scripts\activate.bat" (
  echo Creating virtual environment .venv...
  python -m venv .venv || (
    echo Failed to create virtual environment
    goto :end
  )
)

call ".venv\Scripts\activate.bat"

echo Begin essentials build process...
echo Install requirements using pip
pip install -r requirements.txt

pushd "src\rust_results" || (
  echo Failed to change directory to src\rust_results
  goto :end
)

echo Install required rust libraries using cargo
cargo fetch

echo Build and install results module using maturin
maturin develop --release

popd

echo Build resource files using pyside6-rcc
pyside6-rcc resource.qrc -o src\ui\resources.py
pyside6-rcc resource_init.qrc -o src\ui\resources_init.py

echo OK, everything should run now

:end
endlocal
exit /B 0
