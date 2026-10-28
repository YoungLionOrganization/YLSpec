# Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
"""Regression coverage for draft releases and immutable source/asset boundaries."""
import importlib.util
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

spec = importlib.util.spec_from_file_location("ylspec_release", Path(__file__).resolve().parents[1] / "scripts/release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def run_draft(tmp_path, snapshot, *, ref_exists=True):
    sha = "a" * 40
    calls = []

    def gh(*args):
        calls.append(args)
        if args[:2] == ("api", "repos/owner/project/git/ref/tags/v0.1.1"):
            if not ref_exists:
                raise subprocess.CalledProcessError(1, args)
            return json.dumps({"object": {"type": "commit", "sha": sha}})
        if args[:2] == ("release", "view"):
            return json.dumps({"apiUrl": "https://api.github.com/repos/owner/project/releases/123"})
        if args[:2] == ("api", "https://api.github.com/repos/owner/project/releases/123"):
            return json.dumps(snapshot)
        return "{}"

    with patch.object(release, "gh", side_effect=gh), patch.dict("os.environ", {"GITHUB_REPOSITORY": "owner/project"}):
        release.draft(tmp_path, sha)
    return calls


def test_draft_is_read_by_id_instead_of_published_tag_endpoint(tmp_path):
    calls = run_draft(tmp_path, {"draft": True, "target_commitish": "a" * 40, "assets": []})
    assert any(args[:2] == ("release", "view") for args in calls)
    assert not any("/releases/tags/" in str(arg) for args in calls for arg in args)


def test_empty_unpublished_draft_can_recover_before_first_upload(tmp_path):
    calls = run_draft(tmp_path, {"draft": True, "target_commitish": "b" * 40, "assets": []}, ref_exists=False)
    assert any(args[:2] == ("release", "edit") and "--target" in args for args in calls)
    assert any(args[:2] == ("api", "repos/owner/project/git/refs") and "sha=" + "a" * 40 in args for args in calls)


def test_nonempty_draft_cannot_be_retargeted(tmp_path):
    with pytest.raises(ValueError, match="different source commit"):
        run_draft(tmp_path, {"draft": True, "target_commitish": "b" * 40, "assets": [{"name": "existing.whl"}]})


def test_public_release_cannot_be_replaced(tmp_path):
    with pytest.raises(ValueError, match="already public"):
        run_draft(tmp_path, {"draft": False, "target_commitish": "a" * 40, "assets": []})


def test_existing_asset_hash_must_match(tmp_path):
    artifact = tmp_path / "example.bin"
    artifact.write_bytes(b"verified")
    with pytest.raises(ValueError, match="Existing asset differs"):
        run_draft(tmp_path, {"draft": True, "target_commitish": "a" * 40, "assets": [{"name": artifact.name, "digest": "sha256:" + "0" * 64}]})
