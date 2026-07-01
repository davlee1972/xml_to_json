"""
(c) 2019 David Lee.

Author: David Lee
"""
import decimal
import json
import glob
from multiprocessing import Pool
import subprocess
import os
import gzip
import tarfile
import logging
import sys
from zipfile import ZipFile

import xmlschema
from xmlschema.converters import ColumnarConverter
from xmlschema import XMLResource


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def json_decoder(obj):
    """
    :param obj: python data
    :return: converted type
    :raises:
    """
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S.%f')
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(repr(obj) + " is not JSON serializable")


def open_file(zip, filename):
    """
    :param zip: whether to open a new file using gzip
    :param filename: name of new file
    :return: file handlers
    """
    if zip:
        return gzip.open(filename, "wb")
    else:
        return open(filename, "wb")


def parse_xml(xml_file, lazy, json_file, xml_schema, xpath, xpath_items, output_format, processed, from_zip):
    """
    :param xml_file: xml file
    :param xpath: whether to parse a specific xml path
    :param json_file: json file
    :param my_schema: xmlschema object
    :param output_format: jsonl or json
    :param from_zip: if data is from a file in a zip archive
    :return: data found and processed
    """

    xml_file_resource = XMLResource(xml_file, lazy=lazy, thin_lazy=True)
    
    if xpath:
        xml_iter_decode = xml_schema.iter_decode(xml_file_resource, path=xpath)
    else:
        xml_iter_decode = xml_schema.iter_decode(xml_file_resource)

    if xpath_items:
        root = xpath_items[-1]
    else:
        root = None

    for xml_dict in xml_iter_decode:
        if root:
            xml_dict = xml_dict[root]
        try:
            xml_json = json.dumps(xml_dict, default=json_decoder)
        except Exception as ex:
            _logger.debug(ex)
            pass
        if len(xml_json) > 0:
            if not processed:
                processed = True
                json_file.write(bytes(xml_json, "utf-8"))
            else:
                if output_format == "json":
                    json_file.write(bytes("," + os.linesep + xml_json, "utf-8"))
                else:
                    json_file.write(bytes(os.linesep + xml_json, "utf-8"))
    return processed


def parse_file(input_file, output_file, xsd_file, output_format, zip, xpath, target_path=None, delete_xml=False):
    """
    :param input_file: input file
    :param output_file: output file
    :param xsd_file: xsd file
    :param output_format: jsonl or json
    :param zip: zip save file
    :param xpath: whether to parse a specific xml path
    :param target_path: directory to save file
    :param delete_xml: optional delete xml file after converting
    """

    _logger.debug("Generating schema from " + xsd_file)

    xml_schema = xmlschema.XMLSchema(xsd_file, converter=ColumnarConverter)

    _logger.debug("Parsing " + input_file)

    _logger.debug("Writing to file " + output_file)

    if xpath:
        xpath_items = xpath.split("/")
        lazy = len(xpath_items) - 2
        if lazy < 0:
            lazy = False
    else:
        lazy = False
        xpath_items = []

    processed = False

    with open_file(zip, output_file) as json_file:

        if input_file.endswith((".zip", ".tar.gz")) and output_format == "json":
            json_file.write(bytes("[" + os.linesep, "utf-8"))

        if input_file.endswith(".tar.gz"):
            zip_file = tarfile.open(input_file, 'r')
            zip_file_list = zip_file.getmembers()

            for member in zip_file_list:
                with zip_file.extractfile(member) as xml_file:
                    processed = parse_xml(xml_file, lazy, json_file, xml_schema, xpath, xpath_items, output_format, processed, from_zip=True)

        elif input_file.endswith(".zip"):
            zip_file = ZipFile(input_file, 'r')
            zip_file_list = zip_file.infolist()

            for i in range(len(zip_file_list)):
                with zip_file.open(zip_file_list[i].filename) as xml_file:
                    processed = parse_xml(xml_file, lazy, json_file, xml_schema, xpath, xpath_items, output_format, processed, from_zip=True)
        
        elif input_file.endswith(".gz"):
            with gzip.open(input_file) as xml_file:
                processed = parse_xml(xml_file, lazy, json_file, xml_schema, xpath, xpath_items, output_format, processed, from_zip=False)

        else:
            processed = parse_xml(input_file, lazy, json_file, xml_schema, xpath, xpath_items, output_format, processed, from_zip=False)

        if input_file.endswith((".zip", ".tar.gz")) and output_format == "json":
            json_file.write(bytes(os.linesep + "]", "utf-8"))

    # Remove file if no json is generated
    if not processed:
        os.remove(output_file)
        _logger.debug("No data found in " + input_file)
        return

    if delete_xml:
        os.remove(input_file)

    _logger.debug("Completed " + input_file)


def convert_xml(xsd_file=None, output_format="jsonl", target_path=None, zip=False, xpath=None, multi=1, no_overwrite=False, verbose="DEBUG", log=None, delete_xml=None, xml_files=None):
    """
    :param xsd_file: xsd file name
    :param output_format: jsonl or json
    :param target_path: directory to save file
    :param zip: zip save file
    :param xpath: whether to parse a specific xml path
    :param multi: how many files to convert concurrently
    :param no_overwrite: overwrite target file
    :param verbose: stdout log messaging level
    :param log: optional log file
    :param delete_xml: optional delete xml file after converting
    :param xml_files: list of xml_files

    """

    formatter = logging.Formatter("%(levelname)s - %(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(logging.getLevelName(verbose))
    _logger.addHandler(ch)

    if log:
        # create log file handler and set level to debug
        fh = logging.FileHandler(log)
        fh.setFormatter(formatter)
        fh.setLevel(logging.DEBUG)
        _logger.addHandler(fh)

    _logger.info("Parsing XML Files..")

    if target_path and not os.path.exists(target_path):
        _logger.error("invalid target_path specified")
        sys.exit(1)

    # open target files
    file_list = list(set([f for _files in [glob.glob(xml_files[x]) for x in range(0, len(xml_files))] for f in _files]))
    file_count = len(file_list)

    if multi > 1:
        parse_queue_pool = Pool(processes=multi)

    _logger.info("Processing " + str(file_count) + " files")

    if 1 < len(file_list) <= 1000:
        file_list.sort(key=os.path.getsize, reverse=True)
        _logger.info("Parsing files in the following order:")
        _logger.info(file_list)

    for filename in file_list:

        path, xml_file = os.path.split(os.path.realpath(filename))
        
        output_file = xml_file

        if output_file.endswith(".gz"):
            output_file = output_file[:-3]

        if output_file.endswith(".tar"):
            output_file = output_file[:-4]

        if output_file.endswith(".zip"):
            output_file = output_file[:-4]

        if output_file.endswith(".xml"):
            output_file = output_file[:-4]

        if output_format == "jsonl":
            output_file = output_file + ".jsonl"
        else:
            output_file = output_file + ".json"

        if zip:
            output_file = output_file + ".gz"

        if target_path:
            output_file = os.path.join(target_path, output_file)
            if no_overwrite and os.path.isfile(output_file):
                _logger.debug("No overwrite. Skipping " + xml_file)
                continue
        else:
            output_file = os.path.join(path, output_file)
            if no_overwrite and os.path.isfile(output_file):
                _logger.debug("No overwrite. Skipping " + xml_file)
                continue

        if multi > 1:
            parse_queue_pool.apply_async(parse_file, args=(filename, output_file, xsd_file, output_format, zip, xpath, target_path, delete_xml), error_callback=_logger.info)
        else:
            parse_file(filename, output_file, xsd_file, output_format, zip, xpath, target_path, delete_xml)

    if multi > 1:
        parse_queue_pool.close()
        parse_queue_pool.join()