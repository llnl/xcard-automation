from xcard_automation.core.schema_bundle import default_bundle_path, load_bundle


def test_default_bundle_is_genesis_v1_2() -> None:
    bundle = load_bundle(default_bundle_path())

    assert bundle.id == "genesis_datacard"
    assert bundle.version == "1.2"
    assert bundle.template_path.is_file()
    assert bundle.schema_path.name == "genesis_datacard.yaml"
    assert bundle.schema_path.parent.parent.name == "1.2"
    assert bundle.ontology_path is not None
    assert bundle.ontology_path.is_file()
