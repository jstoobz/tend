import re

import pytest

from tend import model


def test_new_run_id_matches_timestamp_and_suffix_shape():
    run_id = model.new_run_id()

    assert re.fullmatch(r"\d{8}-\d{6}-[a-z0-9]{6}", run_id)


def test_new_run_id_is_unique_across_calls():
    assert model.new_run_id() != model.new_run_id()


def test_slugify_normalizes_a_name():
    assert model.slugify("Bob's Bakery!") == "bobs-bakery"


def test_slugify_strips_scheme_and_www_from_a_url():
    assert model.slugify("https://www.example.com/") == "example-com"


def test_slugify_folds_accents_and_typographic_apostrophes_to_ascii():
    assert model.slugify("Bob's Café & Bakery") == "bobs-cafe-bakery"
    assert model.slugify("José's Autohaus — München") == "joses-autohaus-munchen"


def test_slugify_rejects_empty_input():
    with pytest.raises(ValueError):
        model.slugify("   ")


def test_slugify_rejects_input_with_no_ascii_foldable_characters():
    with pytest.raises(ValueError):
        model.slugify("北京烤鸭店")


def test_site_record_carries_schema_version_and_fields():
    record = model.site_record(name="Bob's Bakery", url="https://example.com")

    assert record["schema_version"] == model.SCHEMA_VERSION
    assert record["slug"] == "bobs-bakery"
    assert record["url"] == "https://example.com"
    assert "created_at" in record


def test_run_manifest_starts_in_running_status():
    manifest = model.run_manifest(run_id="20260702-070000-abc123", site_slug="bobs-bakery")

    assert manifest["schema_version"] == model.SCHEMA_VERSION
    assert manifest["status"] == "running"
    assert manifest["finished_at"] is None
    assert manifest["checks"] == []


def test_finalize_run_manifest_sets_status_and_checks():
    manifest = model.run_manifest(run_id="20260702-070000-abc123", site_slug="bobs-bakery")
    checks = [{"name": "onpage", "ok": True}]

    finalized = model.finalize_run_manifest(manifest, checks=checks)

    assert finalized["status"] == "complete"
    assert finalized["checks"] == checks
    assert finalized["finished_at"] is not None
