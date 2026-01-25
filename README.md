<div align="center">
  <img src="icons/icon.png" alt="Logo" height="200px">
  <h1>JJ ARDFEvent</h1>

  <p>
    <b>Česky</b> | <a href="README_en.md">English</a>
  </p>

  <p>
    <img src="https://img.shields.io/github/v/tag/ARDFEvent/ARDFEvent" alt="GitHub Release">
    <img src="https://img.shields.io/github/license/ARDFEvent/ARDFEvent" alt="GitHub License">
    <img src="https://wakapi.dev/api/badge/jacobcz/interval:30_days/project:ARDFEvent?label=last%2030%20days" alt="Wakapi Time">
  </p>

  <p>
    <b>Otevřený software pro zpracovávání výsledků v ROB.</b><br>
    Navržen tak, aby byl co nejjednodušší a co nejvíce usnadnil práci ajťákům. :sparkles:
  </p>

  <p>
    Autor kódu: Jakub Jiroutek :man_technologist:, autor loga: Dan Zeman :art:
  </p>
</div>

Program je určený pro použití na počítači/notebooku s myší a klávesnicí. Chcete-li program pouze pro Android,
použijte [kolskypavel/Radio-O-Manager](https://github.com/kolskypavel/Radio-O-Manager).

## Funkce programu :toolbox:

1. [x] správa dat závodu (závodníci, kategorie, kontroly)
2. [x] vyčítání SI čipů (všechny verze)
3. [x] tisk lístků na tiskárně podporující ESC-POS (lístek pro závodníka i na šňůru)
4. [x] 100% integrace s ROBis (přes otevřený plugin)
5. [x] export výsledků do různých formátů (CSV, HTML, IOF XML, ARDF JSON)
6. [x] import závodníků a kategorií z CSV
7. [x] sledování závodníků v lese a vypršení jejich limitu
8. [x] víceetapové závody (přes otevřený plugin)
9. [x] webový server pro závodníky v cíli (v případě, že v cíli nejsou mobilní data)
10. [x] startovní čísla
11. [x] startovku (včetně zábrany startu po sobě závodníků jednoho klubu ve stejné kategorii)
12. [x] integrace s OChecklist
13. [x] spojování kontrol
14. [x] multiplatformní (Linux, Windows, macOS)
15. [x] lokalizace (čeština, angličtina)
16. [x] systém pluginů pro rozšíření funkcí

## Instalace :wrench:

### Běžné sestavení

Nejdříve si stáhněte nejnovější verzi programu [odsud](https://github.com/ARDFEvent/ARDFEvent/releases).
Vyberte si balíček pro váš operační systém. Potom pokračujte podle instrukcí níže.

Sestavuju pouze balíčky pro:

- Windows 10 a novější (x64)
- Linux (x64)

Ostatní viz kapitola Pokročilé.

#### Windows

Pro Windows je dostupný instalační program.

1. Stáhněte si soubor `ARDFEvent-<verze>-winx64.exe`.
2. Spusťte instalační program a postupujte podle instrukcí na obrazovce.
3. Po dokončení instalace spusťte program z nabídky Start nebo plochy.

#### Linux :penguin:

Pro Linux je dostupný gzipovaný tarball soubor obsahující předkompilovanou aplikaci.

1. Stáhněte si soubor `ARDFEvent-<verze>-anylinuxx64.tar.gz`.
2. Rozbalte zip soubor do vámi zvoleného adresáře.
3. Otevřete terminál a přejděte do rozbaleného adresáře.
4. Spusťte program příkazem:

```shell
./ARDFEvent
```

### Pokročilé

Pokud váš operační systém není mezi výše uvedenými (mělo by jít v podstatě na čemkoli na čem jde Qt a Rust toolchain,
nejde na Android ani iOS),
nebo chcete program přizpůsobit sami, postupujte podle následujících
kroků:

Pro vlastní sestavení je potřeba:

- Python 3.12 nebo novější :snake:
- Rust toolchain (rustc 1.92.0 nebo novější) :crab:
- git

1. Ujistěte se, že máte všechny požadavky pro vlastní sestavení (viz výše).
2. Zklonujte repozitář z GitHubu:

```shell
git clone https://github.com/ARDFEvent/ARDFEvent.git
```

3. Přejděte do adresáře projektu:

```shell
cd ARDFEvent
```

4. Spusťte skript pro sestavení binárních součástí.

```shell
# Linux / macOS (bash/zsh)
bash build.sh

# Windows (CMD)
build.bat
```

5. Přepněte se do virtuálního prostředí:

```shell
# Linux / macOS
source .venv/bin/activate

# Windows (CMD)
.\.venv\Scripts\activate
```

6. Program spusťte příkazem:

```shell
python src/main.py
```

## Podpora :handshake:

Jste-li členem AROB ČR a nemáte účet na GitHubu, můžete chyby a návrhy hlásit i na emailovou adresu dostupnou
na [mém profilu v ROBisu](https://rob-is.cz/ucet/1494) (musíte být přihlášeni).

Všechny chyby prosím hlaste přes [GitHub Issues](https://github.com/ARDFEvent/ARDFEvent/issues).
Pokud máte nápad na novou funkci, také ji tam můžete přidat jako návrh.

Akutní problémy hlaste také na Issues, přijde mi mailové upozornění.

Na závody, kde jsem přihlášený máte IT podporu zajištěnou :smile:.

## Dokumentace :book:

Dokumentace je dostupná [zde](https://github.com/ARDFEvent/ARDFEvent/wiki) (GitHub wiki).

## Testování :test_tube:

Pro spuštění testů je potřeba mít nainstalovaný `pytest` a `pytest-qt` (obojí v `requirements.txt`). Potom spusťte
příkaz:

```shell
pytest -q
```