import json

from tend import store


def test_atomic_write_json_round_trips(tmp_path):
    path = tmp_path / "record.json"

    store.atomic_write_json(path, {"a": 1})

    assert json.loads(path.read_text()) == {"a": 1}


def test_atomic_write_json_leaves_no_tmp_file_behind(tmp_path):
    path = tmp_path / "record.json"

    store.atomic_write_json(path, {"a": 1})

    leftovers = [p for p in tmp_path.iterdir() if p.name != "record.json"]
    assert leftovers == []


def test_read_json_reads_back_what_was_written(tmp_path):
    path = tmp_path / "record.json"
    store.atomic_write_json(path, {"b": 2})

    assert store.read_json(path) == {"b": 2}


def test_swap_symlink_points_to_target(tmp_path):
    target = tmp_path / "run-1"
    target.mkdir()
    link = tmp_path / "latest"

    store.swap_symlink(link, target)

    assert link.is_symlink()
    assert link.resolve() == target.resolve()


def test_swap_symlink_replaces_existing_link_atomically(tmp_path):
    target1 = tmp_path / "run-1"
    target1.mkdir()
    target2 = tmp_path / "run-2"
    target2.mkdir()
    link = tmp_path / "latest"
    store.swap_symlink(link, target1)

    store.swap_symlink(link, target2)

    assert link.resolve() == target2.resolve()
    leftovers = [p for p in tmp_path.iterdir() if p.name not in {"run-1", "run-2", "latest"}]
    assert leftovers == []
