Dokumentace JJ ARDFEvent
========================
.. sectionauthor:: Jakub Jiroutek <jiroutekja@seznam.cz>

JJ ARDFEvent je aplikace pro organizaci závodů v ROB. Byla vytvořena pro co nejjednodušší použití organizátory. Běží multiplatformně (Windows 10+, Linux, MacOS). Vyvíjí ji ve volném čase Jakub Jiroutek (ELB0904).

.. tip:: Projděte si :doc:`tutoriál <tutorial>`.

Seznam zajímavých funkcí
------------------------

- jednoduché a intuitivní ovládání
- 90% integrace s ROBisem (přihlášky, kategorie, živé výsledky, konečné výsledky, chybí - bude v budoucnu: stahování mezičasů z radiokontrol, nahrávání startovky)
- nativní podpora SPORTidentu - vyčítací krabičky
- startovka a losování (i s rozházením klubů - pokud je to matematicky možné, 2 závodnici stejného klubu nebudou v jedné kategorii startovat po sobě)
- zpracování souboru z O Checklist - změny čipů a přehled reálně odstartovaných závodníků přimo ze startu
- import z CSV
- export výsledků a mezičasů do přispůsobitelného HTML, IOF XML a ARDF JSON
- export startovky do přispůsobitelného HTML, IOF XML a CSV pro ROBis
- správa více závodů najednou (na více readerů) - vyzkoušeno na KP LK
- tisknutí lístků pomocí protokolu ESCPOS - podporuje většinu USB termotiskáren
- přehledný výčet - lístek obsahuje mimo mezičasů i analýzu výsledku závodníka a srovnání s ostatními
- podpora dvojtisku na šnůru - lístek na šnůru neobsahuje zbytečné informace
- přehledná dokumentace a podpora pro organizátory zdarma
- JE ZCELA OTEVŘENÝ A ZDARMA (A TO SE VYPLATÍ! 🤑🏃🏾‍➡️)

Plánované funkce
----------------

- podpora pro nahrávání mezičasů z radiokontrol z ROBisu
- podpora pro automatizované nahrávání startovky do ROBisu
- možnost připojení více počítačů
- okno spíkra
- výsledkové tabule
- překlad do angličtiny
- podpora startovních čísel a národností
- automatické stahování a nahrávání souboru z O Checklistu přes FTP nebo HTTP server 
- etapové závody, štafety a plná podpora sprintu

.. toctree::
   :maxdepth: 3
   :caption: Contents:
   :hidden:

   tutorial.rst

