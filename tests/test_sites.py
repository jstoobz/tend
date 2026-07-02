import pytest

from tend import sites


def test_track_creates_a_site_record(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))

    record = sites.track(name="Bob's Bakery", url="https://example.com")

    assert record["slug"] == "bobs-bakery"
    assert sites.get_site("bobs-bakery") == record


def test_list_sites_returns_tracked_sites_sorted_by_slug(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))
    sites.track(name="Zeta Co", url="https://zeta.example.com")
    sites.track(name="Alpha Co", url="https://alpha.example.com")

    result = sites.list_sites()

    assert [r["slug"] for r in result] == ["alpha-co", "zeta-co"]


def test_list_sites_empty_when_none_tracked(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))

    assert sites.list_sites() == []


def test_get_site_raises_for_unknown_slug(tmp_path, monkeypatch):
    monkeypatch.setenv("TEND_HOME", str(tmp_path))

    with pytest.raises(FileNotFoundError):
        sites.get_site("nope")
