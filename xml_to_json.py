#
# MIT License
#
# Copyright (c) 2026 David Lee
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse

from xml_to_json.convert_xml_to_json import convert_xml_to_json

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="XML To JSON Parser")
    parser.add_argument("-x", "--xsd_file", required=True, help="xsd file name")
    parser.add_argument("-o", "--output_format", default="jsonl", help="output format json or jsonl. Default is jsonl.")
    parser.add_argument("-s", "--server", help="server with hadoop client installed if hadoop not installed")
    parser.add_argument("-t", "--target_path", help="target path. hdfs targets require hadoop client installation. Examples: /proj/test, hdfs:///proj/test, hdfs://halfarm/proj/test")
    parser.add_argument("-z", "--zip", action="store_true", help="gzip output file")
    parser.add_argument("-p", "--xpath", help="xpath to parse out.")
    parser.add_argument("-m", "--multi", type=int, default=1, help="number of parsers. Default is 1.")
    parser.add_argument("-l", "--log", help="log file")
    parser.add_argument("-v", "--verbose", default="DEBUG", help="verbose output level. INFO, DEBUG, etc.")
    parser.add_argument("-n", "--no_overwrite", action="store_true", help="do not overwrite output file if it exists already")
    parser.add_argument("xml_files", nargs=argparse.REMAINDER, help="xml files to convert")

    args = parser.parse_args()

    convert_xml_to_json(args.xsd_file, args.output_format, args.server, args.target_path, args.zip, args.xpath, args.multi, args.no_overwrite, args.verbose, args.log, args.xml_files)

