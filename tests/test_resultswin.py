from datetime import datetime

from models import Punch
from ui.resultswin import ResultsWindow


def test_results_window_shows_categories(qtbot, fake_mw, file_session, make_category, race_engine_file, make_runner):
    # The fixture race_engine_file already creates tables and populates basic_info.
    # We must point the fake_mw to the file engine.
    fake_mw.db = race_engine_file

    c1 = make_category(name="Cat1", sess=file_session)
    r1 = make_runner(category=c1, sess=file_session)
    c2 = make_category(name="Cat2", sess=file_session)
    r2 = make_runner(category=c2, sess=file_session)
    # Add start and finish punches to ensure results calculation works
    start_time = datetime(2025, 1, 1, 10, 0, 0)
    finish_time = datetime(2025, 1, 1, 11, 0, 0)
    file_session.add(Punch(si=r1.si, code=1000, time=start_time))
    file_session.add(Punch(si=r1.si, code=1001, time=finish_time))
    file_session.add(Punch(si=r2.si, code=1000, time=start_time))
    file_session.add(Punch(si=r2.si, code=1001, time=finish_time))
    file_session.commit()

    win = ResultsWindow(fake_mw)
    qtbot.addWidget(win)

    # Debug results from calculation
    from results import calculate_category
    res = calculate_category(race_engine_file, "Cat1", True)
    print(f"Results for Cat1: {res}")

    win._show()

    # Check if categories appear in table
    found_categories = []
    for i in range(win.results_table.rowCount()):
        item = win.results_table.item(i, 0)
        if item:
            found_categories.append(item.text())

    assert "Cat1" in found_categories, f"Found categories: {found_categories}. All rows: {[(win.results_table.item(i, 0).text() if win.results_table.item(i, 0) else '') for i in range(win.results_table.rowCount())]}"
    assert "Cat2" in found_categories, f"Found categories: {found_categories}"
