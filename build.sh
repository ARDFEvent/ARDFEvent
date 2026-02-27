Color_Off='\033[0m'
BYellow='\033[1;33m'
BPurple='\033[1;35m'
BRed='\033[1;31m'
BGreen='\033[1;32m'
BIPurple='\033[1;95m'
BIGreen='\033[1;92m'

echo -e "${BIPurple}Cleanup...${Color_Off}"
rm i18n/ARDFEvent_en.qm | true
rm src/ui/resources.py | true
rm src/ui/resources_init.py | true
echo -e "${BIPurple}Create and activate venv...${Color_Off}"
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
source .venv/bin/activate
echo -e "${BIPurple}Begin essentials build process...${Color_Off}"
echo -e "${BPurple}Install requirements using pip${Color_Off}"
pip install -r requirements.txt
echo -e "${BPurple}Checking for system GDAL...${Color_Off}"
if ! command -v gdal-config &> /dev/null; then
    echo -e "${BRed}Error: libgdal-dev is not installed on your system.${Color_Off}"
    echo -e "${BRed}Please run: sudo apt install libgdal-dev (or your distro's equivalent)${Color_Off}"
    exit 1
fi
GDAL_VERSION=$(gdal-config --version)
echo -e "${BGreen}Found system GDAL version: $GDAL_VERSION${Color_Off}"
echo -e "${BIPurple}Installing matching python-gdal bindings...${Color_Off}"
pip install "gdal==$GDAL_VERSION"
cd src/rust_results || exit
echo -e "${BYellow}Install required rust libraries using cargo${Color_Off}"
cargo fetch
echo -e "${BYellow}Build and install results module using maturin${Color_Off}"
maturin develop --release
cd ../..
echo -e "${BYellow}Build language files using pyside6-lrelease${Color_Off}"
pyside6-lrelease i18n/ARDFEvent_en.ts
echo -e "${BYellow}Build resource files using pyside6-rcc${Color_Off}"
pyside6-rcc resource.qrc -o src/ui/resources.py
pyside6-rcc resource_init.qrc -o src/ui/resources_init.py
echo -e "${BIGreen}OK, everything should run now${Color_Off}"
