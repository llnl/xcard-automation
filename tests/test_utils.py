from xcard_automation.core.utils import (
    deep_merge,
    flatten_answers,
    get_path,
    load_yaml_file,
    set_path,
)


def test_nested_paths_round_trip() -> None:
    data: dict[str, object] = {}

    set_path(data, "contacts[0].email", "ada@example.org")

    assert get_path(data, "contacts[0].email") == "ada@example.org"
    assert get_path(data, "contacts[1].email", "missing") == "missing"


def test_flatten_answers_and_deep_merge_preserve_nested_values() -> None:
    flattened = flatten_answers(
        {"contact": {"person": {"email": "ada@example.org"}}}
    )
    merged = deep_merge(
        {"contact": {"person": {"name": "Ada", "email": "old@example.org"}}},
        {"contact": {"person": {"email": "ada@example.org"}}},
    )

    assert flattened == {"contact.person.email": "ada@example.org"}
    assert merged == {
        "contact": {"person": {"name": "Ada", "email": "ada@example.org"}}
    }


def test_load_yaml_file_supports_scalar_values(tmp_path) -> None:
    answers = tmp_path / "answers.yaml"
    answers.write_text(
        "approved: true\nrecord_count: 2\n",
        encoding="utf-8",
    )

    assert load_yaml_file(answers, {}) == {"approved": True, "record_count": 2}
