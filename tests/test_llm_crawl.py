import json
from pathlib import Path
from types import SimpleNamespace

from xcard_automation.core.llm_crawl import build_crawl_manifest, enrich_answers


def test_crawl_manifest_excludes_secrets_and_binary_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Safe", encoding="utf-8")
    (tmp_path / ".env").write_text("API_KEY=secret", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"binary")

    manifest = build_crawl_manifest(tmp_path)

    assert {item["path"]: item["status"] for item in manifest} == {
        ".env": "excluded_secret",
        "README.md": "included",
        "image.png": "excluded_type",
    }


def test_llm_enrichment_applies_only_cited_safe_paths(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "README.md").write_text("source", encoding="utf-8")
    policy = tmp_path / "policy.yaml"
    policy.write_text(
        "llm_safe_paths: [description.summary]\nllm_review_paths: [identification.name]\n",
        encoding="utf-8",
    )
    skill = tmp_path / "SKILL.md"
    skill.write_text("skill", encoding="utf-8")
    monkeypatch.setattr("xcard_automation.core.llm_crawl.default_skill_path", lambda: skill)
    output = {
        "agent": {"name": "Test Model", "version": "1.0.0"},
        "candidates": [
            {
                "path": "description.summary",
                "value": "Cited summary",
                "confidence": 0.9,
                "citations": [{"source": "README.md", "start_line": 1, "end_line": 1}],
            },
            {
                "path": "security.classification",
                "value": "Secret",
                "confidence": 1.0,
                "citations": [{"source": "README.md", "start_line": 1, "end_line": 1}],
            },
        ],
        "proposals": [
            {
                "path": "identification.name",
                "value": "Cited title",
                "confidence": 0.9,
                "citations": [{"source": "README.md", "start_line": 1, "end_line": 1}],
            }
        ],
    }
    monkeypatch.setattr(
        "xcard_automation.core.llm_crawl.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(output), stderr=""),
    )

    run = enrich_answers(
        ["agent"], tmp_path, tmp_path, policy, {}, {}, tmp_path / "request.json"
    )

    assert run.answers["description"]["summary"] == "Cited summary"
    assert "identification" not in run.answers
    assert run.proposals[0]["value"] == "Cited title"
    assert len(run.resolution["accepted"]) == 1
    assert run.resolution["rejected"][0]["reason"] == "path is not approved for LLM enrichment"
