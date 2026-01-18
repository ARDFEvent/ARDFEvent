Tutoriál
########

.. sectionauthor:: Jakub Jiroutek <jiroutekja@seznam.cz>

Tady najdete přesný průvodce organizací okresního přeboru v JJ ARDFEventu.

Založení závodu
***************

Po spuštění JJ ARDFEventu se vám zobrazí takovéto okno:

.. image:: _static/tutorial/1.png
  :height: 300

v něm vyberte :code:`Nový závod` a v :term:`dialogu<dialog>` zadejte ID závodu **bez mezer a zvláštních znaků (jmenuje se tak soubor)** - např. :code:`kp1608`.

Vyskočí vám hlavní okno:

.. image:: _static/tutorial/2.png
  :height: 300

Nastavení závodu s ROBisem
**************************

V kartě :code:`Základní info` nemusíte vyplňovat nic, přejděte rovnou do záložky :code:`ROBis`.

.. caution:: Před stahováním si ověřte, že je vše co se stahuje (název závodu, pásmo, limit, pořadatel a čas statu 00 nastavený u etapy v ROBisu), jinak se to JJ ARDFEventu nebude líbit a bude házet errory

V okně :code:`ROBis` vyplňte všechny požadované údaje a uložte je tlačítkem :code:`OK`.

.. image:: _static/tutorial/4.png
  :height: 300

.. hint::

  **Jak najít požadované údaje v ROBisu**

  - API klíč: najdete u příslušné etapy
  - ID soutěže: (z URL v prohlížeči při otevřeném závodě) :code:`https://rob-is.cz/soutez/39/?race=484&tab=results` => ID soutěže je **39** (484 je ID etapy, JJ ARDFEvent toto číslo nezajímá)
  - Číslo etapy: E2 => číslo etapy je **2**

Pro stažení nastavení závodu, přihlášek a kategorií klikněte na :code:`Stáhnout přihlášky, kategorie`.

.. attention:: Import z ROBisu samozřejmě funguje jen tehdy, když jste připojeni k interetu. Když je připojení pomalé, JJ ARDFEvent na chvíli zamrzne.

V dolním :term:`logu<log>` se zobrazí, které kategorie byly vytvořeny a :code:`Import OK`:

.. image:: _static/tutorial/5.png
  :height: 300

S uložením API klíče se automaticky budou nahrávat živé výsledky na ROBis při vyčítání.

Nastavení závodu bez ROBisu
***************************

Pokud závod nezadáváte do ROBisu, můžete si ho nastavit ručně.
V kartě :code:`Základní info` vyplňte všechny údaje a uložte je tlačítkem :code:`OK`.

Jak přidat kategorie se dozvíte v :ref:`Manuální přidání kategorií`.

CSV import přihlášek
====================

CSV import proběhne po vybrání souboru v kartě :code:`Import`.

Příklad souboru pro import:

.. image:: _static/tutorial/7.png
  :height: 100

.. caution:: Z Excelu/LO exportujte jako CSV s rozdělovníkem :code:`;`.

Zde příklad :term:`logu<log>` po naimportování souboru výše:

.. image:: _static/tutorial/8.png
  :height: 300

.. note:: Klub XXX není v AROB ČR validní, tudíž hází upozornění.

Nastavení kontrol
*****************

Kontroly se nastavují v kartě :code:`Kontroly`:

.. image:: _static/tutorial/9.png
  :height: 300

Buď můžete kontroly přidat ručně kliknutím na :code:`Přidat`, nebo zvolit přednastavené sady kontrol.

.. caution:: Nezapomeňte kliknout vždy před odchodem z karty na :code:`Uložit`!

Vlastnosti kontrol
==================

Jméno kontroly
--------------

Kontrola může mít jákekoliv alfanumerické jméno, pro přehlednost vyčítacího lístku doporučuji
ale maximálně 4 znaky (např. :code:`1`, :code:`R2`, :code:`5F`, :code:`4/R4`, :code:`M` nebo :code:`S`)

SI kód
------

Jakékoliv číslo v :math:`\langle31; 255\rangle`, samozřejmě stejné číslo jako nastavujete v :code:`SI Config+`

Příznaky kontroly
-----------------

Kontrola může být nastavena jako (vzájemně se nevylučují):

- :code:`Povinná` - musí být vyčtena, jinak je závodník diskvalifikován
- :code:`Divácká` - kontrola odděluje okruhy - např. pomalé a rychlé

.. hint:: :code:`S` nastavujte jako povinnou, příznak :code:`Divácká` je zatím nefunkční a nic nemění

Spojování kontrol
-----------------

**V případě, že má více kontrol jednu SI jednotku, je nemožné aby existovaly obě dvě v JJ ARDFEventu**.
Jednoduše vytvořte jednu kontrolu a pojmenujte ji např. :code:`5/R5`. Jak to udělat tak, aby nebylo spojení vidět i na startovce najdete v sekci :ref:`Kategorie + tratě`

Přednastavené sady kontrol
==========================

Sady jsou:

- :code:`Pomalé kontroly`: 1, 2, 3, 4, 5, M - povinná
- :code:`Všechny kontroly`: 1, 2, 3, 4, 5, R1, R2, R3, R4, R5, M - povinná
- :code:`Všechny kontroly`: 1, 2, 3, 4, 5, S - povinná + divácká, R1, R2, R3, R4, R5, M - povinná

Kategorie + tratě
*****************

Kategorie a tratě se nastavují v kartě :code:`Kategorie`.
Jestliže jste stahovali závod z ROBisu, kategorie budou již naimportované.

.. image:: _static/tutorial/10.png
  :height: 300

Manuální přidání kategorií
==========================

Novou kategorii vytvoříte tím, že do :term:`dialogu<dialog>` po kliknutí na :code:`Nová kategorie` zadáte název:

.. image:: _static/tutorial/6.png
  :height: 300

Definování tratě
================

Kontroly (v levém sloupečku) do tratě (v pravém sloupečku) přidáváte dvojklikem v pořadí, v jakém je chcete zobrazovat na výsledcích.
V případě překliku nebo změny tratí se kontrola odebírá dvojklikem v pravém sloupečku.

.. image:: _static/tutorial/11.png
  :height: 300

Kontroly zobrazované před závodem
=================================

Jestliže máte spojené kontroly (např. :code:`4/R4`, viz :ref:`Spojování kontrol`), jako na obrázku výše,
nechcete aby závodníci ze startovky poznali, že je kontrola spojená. Kontroly zobrazované ve startovce
se dají nastavit v poli :code:`Před závodem zobrazované kontroly` v kartě :code:`Kategorie` (pole se
samo nastavuje při přidání kontroly). Ve výše uvedeném případě by jste :code:`1, 2, 4/R4, M` přepsali na
:code:`1, 2, 4, M` a závodníci by tak nepoznali, že je kontrola spojená. Toto musíte provést u každé kategorie.

Startovka
*********

Startovku spravujete v kartě :code:`Startovka`.
Nachází se tam řaditelná tabulka (např. kliknutím na nadpis sloupce :code:`Kategorie`, seřadíte podle kategorie, funguje pro všechny sloupce)

.. image:: _static/tutorial/12.png
  :height: 300

.. tip:: Jestli chcete startovat na krabičku, startovku nelosujte.

.. warning:: Když je vylosovaná startovka a závodník má čas startu v čipu, počítá se čas z čipu.

Losování startovky
==================

.. image:: _static/tutorial/13.png
  :height: 300

V okně losování startovky nastavte startovní interval a časy startu 00 pro každou kategorii a stiskněte :code:`Losovat!`

Startovka se automaticky vylosuje s co největším rozestupem klubů v kategorii.

Export startovky do O Checklist
===============================

Startovka pro O Checklist se exportuje v kartě :code:`Startovka`.

V menu :code:`Exportovat` vyberte :code:`IOF XML 3.0` a přeneste vyexportovaný soubor do telefonu nebo tabletu. Dále postupujte podle `návodu autora <https://stigning.se/checklist/help_en.html#import-start-list>`_

Export startovky pro ROBis
==========================

Startovka pro ROBis se exportuje v kartě :code:`Startovka`.

V menu :code:`Exportovat` vyberte :code:`CSV pro ROBis`. Jak ho nahrát do ROBisu v `oficiální nápovědě ROBisu <https://rob-is.cz/napoveda#event-startlist-results>`_

Vyčítání
********

.. hint:: Pro vyčítání na Windows je zapotřebí `USB ovladač pro SI <https://www.sportident.com/products/usb-driver>`_.

V kartě :code:`Vyčítání` zvolte port SI a tiskárny (nebo :code:`Netisknout`) a v případě tisku na šňůru zvolte :code:`Dvojtisk`.

Po aktivaci vyčítání se zobrazí okno stavu vyčítání:

.. image:: _static/tutorial/15.png
  :height: 300

Tisk lístků pro závodníky
=========================

V případě zvoleného portu tiskárny se po vyčtení závodníka vytiskne lístek.

V případě zvolení :code:`Dvojtisk` se vytisknou dva lístky, jeden pro závodníka a druhý na šňůru (po tisku prvního lístku se zobrazí okno a po potvrzení se vytiskne druhý). Lístek na šnůru neobsahuje zbytečné informace a má na začátku místo pro připnutí na šňuru.

.. image:: _static/tutorial/14.png
  :height: 300

Nalevo lístek na šňůru, napravo pro závodníka.

Případné chybové stavy
======================

Při jakékoliv chybě se přehraje následující zvuk a ve vyčítacím dialogu jeden z následujích stavů:

.. raw:: html

    <audio controls="controls">
      <source src="_static/tutorial/error.wav" type="audio/wav">
      Your browser does not support the <code>audio</code> element.
    </audio>

.. csv-table:: Chybové stavy
    :header: "Stav", "Příčina", "Řešení"

    "CHYBA SI", "Chyba ve čtení čipu, nejčastěji brzo vytažený čip z jednotky.", "Vyčtěte znovu."
    "NENALEZEN ČIP", "Čip není přiřazen závodníkovi v databázi.", "Vyplňte jméno závodníka do zobrazeného dialogu."
    "CHECK ERROR", "Check proběhl více jak hodinu před startem. Je pravděpodobné, že je čip nevymazaný.", "Vyberte, jestli chcete čip vyčíst. [1]_"
    "JIŽ VYČTENÝ ČIP", "Čip již byl vyčten.", "Vyberte, jestli chcete stávající data přepsat."

Závodníci v lese
****************

Seznam závodníků, kteří jsou v lese, se zobrazuje v kartě :code:`Závodníci v lese`.

Závodníci se v tomto seznamu objeví po startu podle startovky a zmizí se po vyčtení čipu.

Import dat z O Checklist
========================

Import dat z O Checklist se provádí v kartě :code:`Závodníci v lese`.

Nejdříve je potřeba dostat soubor :code:`start_status.yaml` z telefonu/tabletu do počítače (např. přes e-mail nebo FTP), poté v kartě :code:`Závodníci v lese` klikněte na :code:`Import z O Checklist` a vyberte soubor :code:`start_status.yaml` (musí se tak jmenovat). Akce začne probíhat hned po vybrání souboru.

Průběh akce vidíte v :term:`logu<log>`.

Výsledky
********

Výsledky se zobrazují v kartě :code:`Výsledky`.

Export výsledků
===============

Export je možný do několika formátů tlačítkem :code:`Exportovat`.

.. csv-table:: Formáty exportu
    :header: "Formát", "Použití"

    "HTML / HTML s mezičasy", "Pro zveřejnění na webu, tisk nebo export přes prohlížeč do PDF."
    "IOF XML 3.0", "Pro nahrání výsledků do aplikací pro OB."
    "ARDF JSON", "Pro nahrání výsledků do ROBisu."
    "CSV", "Pro tisk diplomů a další zpracování ve Excelu/LO."

Výsledkový server
=================

.. versionadded:: 1.0.0
    Přidán webový server.

Webový server se spustí v kartě :code:`Výsledky` tlačítkem :code:`Spustit webový server`.

Webový server najdete na adrese :code:`http://localhost:8080/` (pokud běží na stejném počítači) nebo :code:`http://<IP_ADRESA_SERVERU>:8080` (pokud běží na jiném počítači v síti).

Ve výběru vyberte zobrazované kategorie a klikněte na nastartovat:

.. image:: _static/tutorial/17.png
  :height: 300

.. tip:: Více kategorií vyberete tak, že je vyberete s podrženým :kbd:`Ctrl` nebo :kbd:`Shift`.

Po nastartování se budou vybrané kategorie nekonečně střídat po časovém intervalu spočítaném podle počtu závodníků.

.. image:: _static/tutorial/16.png
  :height: 300

Hlášení
-------

V webovém serveru je možné po vystřídání všech kategorií zobrazit hlášení (např. :code:`Odjezd autobusu v 12:10.`, :code:`Vyhlášení výsledků v 15:00` apod.). Hlášení se nastavuje tlačítkem :code:`Změna hlášení`.

.. image:: _static/tutorial/18.png
  :height: 300

Nahrání finálních výsledků do ROBisu
====================================

V kartě :code:`ROBis` klikněte na :code:`Nahrát výsledky`.

Slovníček cizích pojmů
**********************
.. glossary::

  dialog
    vyskakovací okno

  log
    záznam událostí, které se dějí v programu

.. rubric:: Poznámky pod čarou

.. [1] Pravidla ROB - 23.1: "V předstartovním prostoru: a) je při použití kontrolních jednotek elektronického razícího a měřícího systému závodník povinen provést vymazání čipu v mazací jednotce a následně provést kontrolu jeho vymazání v kontrolní jednotce" - dle pravidel pořadatel čip vyčíst nemusí.