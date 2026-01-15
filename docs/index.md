# Vítejte v dokumentaci k JJ ARDFEventu

Najdete zde popis všech prvků uživatelského rozhraní, tutoriály (jak odvyčítat závod) a možnosti rozšíření programu.

**DOKUMENTACE NENÍ JEŠTĚ DOKONČENA.** První verze dokumentace by měla být hotova do konce února 2026.

## Co je JJ ARDFEvent?

JJ ARDFEvent je otevřený software pro zpracovávání výsledků v ROB.
Je navržen tak, aby co nejvíce usnadnil práci IT a byl co nejjednodušší.

### (Ne moc dlouhá) historie

- listopad 2024 - vzniká první verze (ještě v terminálu, pouze vyčítání SI čipů a tisk lístků)
- prosinec 2024 - přechod na GUI pomocí PySide6, program už ví o existenci závodu (závodníci, kategorie, kontroly),
  počítá výsledky
- leden 2025 - zavedení verzovacího systému Git, vydání kódu na GitHub
- únor 2025 - první zkušební závod v klubovně
- květen 2025 - první ostrý závod - 2x OP Liberec - vyčítání dvou závodů najednou na jednom počítači
- červen 2025 - přidána podpora MS Windows, verze 0.9, další OP
- srpen 2025 - soustředění v Doksech - 10 závodů, spoustu zpětné vazby a nápadů na vylepšení (a taky chyb)
- září 2025 - přidání webserveru, potom na chvilku pauza od vývoje
- říjen 2025 - první nároďák (PP v Písku, paralelně s P. Šrůtou), bezchybné vyčítání cca 2x120 závodníků
- listopad 2025 - program představen v rámci jednoho slidu na konferenci AROB
- prosinec 2025 - překlad do AJ, přidány pluginy (ROBis a víceetapové závody vyčleňeny do samostatných projektů)
- leden 2026 - velká změna UI, začátek dokumentace

### Co umí?

- základní správa závodu (závodníci, kategorie, kontroly)
- vyčítání SI čipů (všechny verze)
- tisk lístků na tiskárně podporující ESC-POS (lístek pro závodníka i na šňůru)
- 100% integrace s ROBis (přes otevřený plugin)
- export výsledků do různých formátů (CSV, HTML, XML)
- import závodníků a kategorií z CSV
- sledování závodníků v lese a vypršení jejich limitu
- víceetapové závody (přes otevřený plugin)
- webový server pro závodníky v cíli
- startovní čísla
- startovku
- integrace s OChecklist
- spojování kontrol
- multiplatformní (Linux, Windows, MacOS)

Vyvíjí a udržuje ho Jakub Jiroutek (ELB0904).

## Jak se v dokumetaci orientovat?

Dokumentace je rozdělena do tří hlavních částí:

Rozpracováno:

- **Uživatelské rozhraní**: Tato část popisuje všechny prvky, které uživatel vidí a používá v aplikaci JJ
  ARDFEvent.
  Najdete zde informace o tlačítkách, menu, formulářích a dalších prvcích uživatelského rozhraní.

V plánu:

- **Tutoriály**: Tato část obsahuje návody a průvodce, které vám pomohou lépe porozumět
  tomu, jak aplikaci používat.
  Najdete zde krok za krokem instrukce pro různé funkce a scénáře použití.
- **Rozšíření**: Tato část je určena pro pokročilejší uživatele, kteří chtějí aplikaci přizpůsobit svým
  potřebám.
  Najdete zde informace o tom, jak vytvářet pluginy pro JJ ARDFEvent. 
