from __future__ import annotations

from typing import Any

import yaml


class CfnLoader(yaml.SafeLoader):
    """Safe YAML loader that preserves CloudFormation intrinsic tags as data."""


def _construct_intrinsic(loader: CfnLoader, suffix: str, node: yaml.Node) -> Any:
    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node)
    else:
        value = loader.construct_mapping(node)

    names = {
        "Ref": "Ref",
        "Sub": "Fn::Sub",
        "GetAtt": "Fn::GetAtt",
        "Join": "Fn::Join",
        "If": "Fn::If",
        "Equals": "Fn::Equals",
        "Not": "Fn::Not",
        "And": "Fn::And",
        "Or": "Fn::Or",
        "FindInMap": "Fn::FindInMap",
        "Select": "Fn::Select",
    }
    key = names.get(suffix, f"Fn::{suffix}")
    if suffix == "GetAtt" and isinstance(value, str) and "." in value:
        value = value.split(".", 1)
    return {key: value}


CfnLoader.add_multi_constructor("!", _construct_intrinsic)


def load_template(text: str) -> dict[str, Any]:
    document = yaml.load(text, Loader=CfnLoader)  # noqa: S506 - SafeLoader subclass only
    if not isinstance(document, dict):
        raise ValueError("template root must be a mapping")
    return document
