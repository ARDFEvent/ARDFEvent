Color_Off='\033[0m'
BYellow='\033[1;33m'
BPurple='\033[1;35m'
BIPurple='\033[1;95m'
BIGreen='\033[1;92m'
BIRed='\033[1;91m'

echo -e "${BIPurple}Cleanup...${Color_Off}"
rm i18n/ARDFEvent_en.qm | true
rm src/ui/resources.py | true
rm src/ui/resources_init.py | true
echo -e "${BIPurple}Create and activate venv...${Color_Off}"
if [ -z "$GITHUB_ACTIONS" ]; then
  if [ ! -d ".venv" ]; then
    python -m venv .venv
  fi
  source .venv/bin/activate
else
  echo "Running in CI: Skipping venv creation"
fi
source .venv/bin/activate
echo -e "${BIPurple}Begin essentials build process...${Color_Off}"
gdal-config --version &> /dev/null || { echo -e "${BIRed}GDAL not found${Color_Off}"; exit 1; }
GDAL_VER=$(gdal-config --version | cut -d' ' -f1)
echo -e "${BIGreen}Installing GDAL $GDAL_VER...${Color_Off}"
pip install "gdal==$GDAL_VER"
echo -e "${BPurple}Install requirements using pip${Color_Off}"
pip install -r requirements.txt
pip install pygobject
cd src/rust_results || exit
echo -e "${BYellow}Install required rust libraries using cargo${Color_Off}"
cargo fetch
echo -e "${BYellow}Build and install results module using maturin${Color_Off}"
maturin build --release --interpreter python
pip install target/wheels/*.whl
cd ../..
echo -e "${BYellow}Build language files using pyside6-lrelease${Color_Off}"
pyside6-lrelease i18n/ARDFEvent_en.ts
echo -e "${BYellow}Build resource files using pyside6-rcc${Color_Off}"
pyside6-rcc resource.qrc -o src/ui/resources.py
pyside6-rcc resource_init.qrc -o src/ui/resources_init.py
echo -e "${BIGreen}OK, everything should run now${Color_Off}"
