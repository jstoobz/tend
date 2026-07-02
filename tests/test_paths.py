from tend import paths


def test_tend_home_override_collapses_all_roots(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))

    assert paths.data_dir() == tmp_path / "data"
    assert paths.config_dir() == tmp_path / "config"
    assert paths.cache_dir() == tmp_path / "cache"
    assert paths.state_dir() == tmp_path / "state"


def test_without_override_falls_back_to_xdg(monkeypatch):
    monkeypatch.delenv("TEND_HOME", raising=False)

    assert "tend" in str(paths.data_dir()).lower()
    assert "tend" in str(paths.config_dir()).lower()


def test_data_dir_is_created_on_demand(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))

    resolved = paths.data_dir(ensure=True)

    assert resolved.is_dir()
