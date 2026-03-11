@echo off
setlocal

echo Cleanup...
del /F /Q "i18n\ARDFEvent_en.qm" 2>nul
del /F /Q "src\ui\resources.py" 2>nul
del /F /Q "src\ui\resources_init.py" 2>nul

echo Begin essentials build process...
echo Install requirements using pip
pip install -r requirements.txt
pip install pywin32

pushd "src\rust_results" || (
  echo Failed to change directory to src\rust_results
  goto :end
)

echo Install required rust libraries using cargo
cargo fetch

echo Build and install results module using maturin
python -m maturin develop --release

popd

echo Build language files using pyside6-lrelease
python -m PySide6.scripts.lrelease i18n\ARDFEvent_en.ts

echo Build resource files using pyside6-rcc
python -m PySide6.scripts.rcc resource.qrc -o src\ui\resources.py
python -m PySide6.scripts.rcc resource_init.qrc -o src\ui\resources_init.py

echo OK, everything should run now

:end
endlocal
exit /B 0
