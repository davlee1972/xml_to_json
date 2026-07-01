import json
import os
import tempfile
import pytest
from xml_to_json.convert_xml_to_json import parse_file


def test_json(snapshot):

    realpath = os.path.dirname(os.path.realpath(__file__))

    input_file = os.path.join(realpath, "data", "PurchaseOrder.xml")
    output_file = os.path.join(tempfile.gettempdir(), "PurchaseOrder.json")
    xsd_file = os.path.join(realpath, "data", "PurchaseOrder.xsd")
    output_format = "json"
    zip = False
    xpath = None

    parse_file(input_file, output_file, xsd_file, output_format, zip, xpath)
    with open(output_file) as f:
        target_json = json.loads(f.read())
    os.remove(output_file)
    assert target_json == snapshot


def test_jsonl(snapshot):

    realpath = os.path.dirname(os.path.realpath(__file__))

    input_file = os.path.join(realpath, "data", "PurchaseOrder.xml")
    output_file = os.path.join(tempfile.gettempdir(), "PurchaseOrder.jsonl")
    xsd_file = os.path.join(realpath, "data", "PurchaseOrder.xsd")
    output_format = "jsonl"
    zip = False
    xpath = "/purchaseOrder/items/item"

    test_json = list()
    target_json = list()

    parse_file(input_file, output_file, xsd_file, output_format, zip, xpath)
    with open(output_file) as f:
        for line in f:
            target_json.append(json.loads(line))
    os.remove(output_file)
    assert target_json == snapshot