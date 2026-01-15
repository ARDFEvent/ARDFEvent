import json
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtWidgets import QInputDialog
from dulwich import porcelain

from ui.pluginmanagerwin import PluginManagerWindow


def _make_plugin_dir(base: Path, name: str, meta: dict):
    d = base / ".ardfevent" / "plugins" / name
    d.mkdir(parents=True, exist_ok=True)
    p = d / "plugin.json"
    p.write_text(json.dumps(meta, ensure_ascii=False))
    return p


def test_show_populates_table(tmp_path, qtbot, monkeypatch):
    # Arrange: make a fake plugins folder under home
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    meta1 = {"name": "Plugin A", "version": "1.0", "description": "Desc A", "author": "Alice"}
    meta2 = {"name": "Plugin B", "version": "2.0", "description": "Desc B", "author": "Bob"}

    _make_plugin_dir(tmp_path, "pluginA", meta1)
    _make_plugin_dir(tmp_path, "pluginB", meta2)

    mw = SimpleNamespace()
    mw.pl = SimpleNamespace(load_plugin=lambda p: None)

    win = PluginManagerWindow(mw)
    qtbot.addWidget(win)

    win.show()

    assert win.table.rowCount() == 2
    names = {win.table.item(i, 0).text() for i in range(win.table.rowCount())}
    assert names == {"Plugin A", "Plugin B"}


def test_update_calls_pull_for_each_plugin(tmp_path, qtbot, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _make_plugin_dir(tmp_path, "p1", {"name": "P1", "version": "1", "description": "", "author": ""})
    _make_plugin_dir(tmp_path, "p2", {"name": "P2", "version": "1", "description": "", "author": ""})

    mw = SimpleNamespace()
    mw.pl = SimpleNamespace(load_plugin=lambda p: None)

    calls = []

    def fake_pull(repo):
        calls.append(repo)

    monkeypatch.setattr(porcelain, "Repo", lambda path: path)
    monkeypatch.setattr(porcelain, "pull", fake_pull)

    win = PluginManagerWindow(mw)
    qtbot.addWidget(win)

    win._update()

    assert len(calls) >= 2


def test_install_plugin_clones_and_loads(tmp_path, qtbot, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    url = "https://example.com/foo.git"

    monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: (url, True))

    clone_calls = []

    def fake_clone(repo_url, dest_path):
        clone_calls.append((repo_url, Path(dest_path)))
        dest_path.mkdir(parents=True, exist_ok=True)
        (Path(dest_path) / "plugin.json").write_text(json.dumps({
            "name": "Cloned", "version": "0.1", "description": "cloned", "author": "me"
        }))

    monkeypatch.setattr(porcelain, "clone", fake_clone)

    loaded = []

    def fake_load_plugin(path):
        loaded.append(Path(path).name)

    mw = SimpleNamespace()
    mw.pl = SimpleNamespace(load_plugin=fake_load_plugin)

    win = PluginManagerWindow(mw)
    qtbot.addWidget(win)

    win._install_plugin()

    assert clone_calls, "porcelain.clone was not called"
    assert loaded, "mw.pl.load_plugin was not called"

    assert win.table.rowCount() >= 1
