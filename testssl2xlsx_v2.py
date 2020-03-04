#!/usr/bin/env python3
#    Copyright 2017 - 2018 Alexandre Teyar

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this output_file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
#    limitations under the License.

import argparse
import json
import logging
import sys
import time
import xlsxwriter
import re

# custom levels for the logging lib
RESULT = 21

# minimal acceptable cipher bits; ciphers with lower bits get reported in the Excel
min_acceptable_cipher_bits = 129

# add or remove entries from the lists below in order to enable/disable
# reporting for the selected entries - respect the case -
certificates = {
    "cert_chain_of_trust": {
        "name": "Chain of Trust"
    },
    "cert_expiration_status": {
        "name": "Expiration Status"
    },
    "cert_signatureAlgorithm": {
        "name": "Signature Algorithm"
    },
    "cert_trust": {
        "name": "Trust"
    }
}
protocols = sorted([
    "SSLv2",
    "SSLv3",
    "TLS1",
    "TLS1_1",
    "TLS1_2",
    "TLS1_3"
])
vulnerabilities = {
    "BEAST": {
        "name": "BEAST"
    },
    "BREACH": {
        "name": "BREACH"
    },
    "CRIME_TLS": {
        "name": "CRIME"
    },
    "fallback_SCSV": {
        "name": "Fallback SCSV"
    },
    "FREAK": {
        "name": "FREAK"
    },
    "LOGJAM": {
        "name": "Logjam"
    },
    "LUCKY13": {
        "name": "Lucky13"
    },
    "POODLE_SSL": {
        "name": "POODLE"
    },
    "RC4": {
        "name": "RC4"
    },
    "ROBOT": {
        "name": "ROBOT"
    },
    "secure_client_renego": {
        "name": "Secure Client Renegotiation"
    },
    "SWEET32": {
        "name": "Sweet32"
    },
    "heartbleed": {
        "name": "Heartbleed"
    },
    "CCS": {
        "name": "CCS"
    },
    "ticketbleed": {
        "name": "ticketbleed"
    },
    "secure_renego": {
        "name": "Secure Renegotiation"
    },
    "DROWN": {
        "name": "DROWN"
    },
    "LOGJAM": {
        "name": "LOGJAM"
    },
    "LOGJAM-common_primes": {
        "name": "LOGJAM - common_primes"
    },
    "BEAST_CBC_TLS1": {
        "name": "BEAST_CBC_TLS1"
    }
}

ciphers = {
    "cipherlist_NULL": {
        "name": "cipherlist_NULL: Ciphers, offering no encryption"
    },
    "cipherlist_aNULL": {
        "name": "cipherlist_aNULL: Anonymous DH/ECDH supported"
    },
    "cipherlist_EXPORT": {
        "name": "cipherlist_EXPORT: Export encryption algorithms (40/50 bit)"
    },
    "cipherlist_DES+64Bit": {
        "name": "cipherlist_DES+64Bit"
    },
    "cipherlist_128Bit": {
        "name": "cipherlist_128Bit"
    },
    "cipherlist_3DES": {
        "name": "cipherlist_3DES"
    },
    "cipherlist_HIGH": {
        "name": "cipherlist_HIGH: Key lengths larger 128 bits"
    },
    "cipherlist_STRONG": {
        "name": "cipherlist_STRONG"
    }
}

def parse_args():
    """ Parse and validate the command line
    """
    parser = argparse.ArgumentParser(
        description=(
            "Parse testssl pretty JSON files into an Excel spreadsheet for "
            "quicker and easier reporting"
        )
    )

    parser.add_argument(
        "-iJ",
        "--input-json",
        dest="input_file",
        help="pretty JSON file containing the testssl results",
        required=True,
        type=argparse.FileType('r')
    )

    parser.add_argument(
        "-oX",
        "--output-xlsx",
        dest="output_file",
        help="XLSX file containing the output results",
        required=False,
        type=str
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const=logging.DEBUG,
        default=logging.INFO,
        dest="loglevel",
        help="enable verbosity",
        required=False
    )

    return parser.parse_args()

def insert(headers, d):
    """ Insert values at the appropriate index
    """
    data = ["N/A"] * len(headers)

    for key, values in d.items():
        if isinstance(values, dict):
            data[headers.index(values["name"])] = values.get("severity")
        else:
            data[headers.index(key)] = values

    return data

def insert2(headers, d, min_bits):
    """ Insert values at the appropriate index for parse_host_cipherTests
    """
    data = [""] * len(headers)

    for key, values in d.items():
      try:
        if isinstance(values, dict):
            text = values.get("severity")[::-1]
            bits = re.split(r' +', values.get("severity"))[-2]
            bits = int(filter(str.isdigit, str(bits)))
            cipher = re.split(r' +', values.get("severity"))[1]

            if bits < min_bits:
                data[headers.index(values["name"])] += "%s [%d bits]\n" % (cipher,bits)
        else:
            data[headers.index(key)] = values
      except:
      	print "Skipping - Parsing error"
      	data[headers.index(values["name"])] += "-- Parsing Error --\n"
    return data


def draw_table(worksheet, table_headers, table_data):
    """ Create an Excel worksheet containing the 'table_headers'
        and 'table_data' dataset
    """
    column_count = 0
    row_count = 0
    table_column_count = len(table_headers) - 1
    table_row_count = len(table_data)

    logging.debug("{}".format(table_headers))
    logging.debug("{}".format(table_data))

    worksheet.add_table(
        row_count,
        column_count,
        table_row_count,
        table_column_count,
        {
            "banded_rows": True,
            "columns": table_headers,
            "data": table_data,
            "first_column": True,
            "style": "Table Style Medium 1"
        }
    )


def parse_host_certificate(workbook, data):
    table_data = []
    table_headers = [
        {"header": "Host IP"},
        {"header": "Port"},
        {"header": "Vulnerability"},
        {"header": "Severity"},
        {"header": "Information"}
    ]

    for values in data["scanResult"]:
        for serverDefault in values["serverDefaults"]:
            if serverDefault["id"] in certificates.keys():
                table_data.append(
                    [
                        values["ip"],
                        int(values["port"]),
                        certificates[serverDefault["id"]]["name"],
                        serverDefault["severity"],
                        serverDefault["finding"]
                    ]
                )

    worksheet = workbook.add_worksheet("Host vs Certificate")
    draw_table(worksheet, table_headers, table_data)

def parse_host_certificates(workbook, data):
    table_data = []
    table_headers = [
        {"header": "Host IP"},
        {"header": "Port"}
    ]

    for values in certificates.values():
        table_headers.append({"header": values["name"]})

    for values in data["scanResult"]:
        d = {
            "Host IP": values["ip"],
            "Port": int(values["port"])
        }

        for serverDefault in values["serverDefaults"]:
            if serverDefault["id"] in certificates.keys():
                d[serverDefault["id"]] = {
                    "name": certificates[serverDefault["id"]]["name"],
                    "severity": serverDefault["severity"]
                }

        table_data.append(insert([x["header"] for x in table_headers], d))

    worksheet = workbook.add_worksheet("Host vs Certificates")
    draw_table(worksheet, table_headers, table_data)


def parse_host_protocol(workbook, data):
    table_data = []
    table_headers = [
        {"header": "Host IP"},
        {"header": "Port"},
        {"header": "Supported Protocol"},
        {"header": "Severity"}
    ]

    for values in data["scanResult"]:
        for protocol in values["protocols"]:
            if protocol["id"] in protocols:
                if "offered" in protocol["finding"]:
                    table_data.append(
                        [
                            values["ip"],
                            int(values["port"]),
                            protocol["id"],
                            protocol["severity"]
                        ]
                    )

    worksheet = workbook.add_worksheet("Host vs Protocol")
    draw_table(worksheet, table_headers, table_data)


def parse_host_protocols(workbook, data):
    table_data = []
    table_headers = [
        {"header": "Host IP"},
        {"header": "Port"}
    ]

    for protocol in protocols:
        table_headers.append({"header": protocol})

    for values in data["scanResult"]:
        d = {
            "Host IP": values["ip"],
            "Port": int(values["port"])
        }

        for protocol in values["protocols"]:
            if protocol["id"] in protocols:
                if protocol["finding"] == "offered" or protocol["finding"] == "offered (deprecated)":
                    d[protocol["id"]] = "YES"
                else:
                    d[protocol["id"]] = "NO"

        table_data.append(insert([x["header"] for x in table_headers], d))

    worksheet = workbook.add_worksheet("Host vs Protocols")
    draw_table(worksheet, table_headers, table_data)


def parse_host_vulnerability(workbook, data):
    table_data = []
    vcenter = workbook.add_format({"valign": "vcenter"})
    table_headers = [
        {
            "header": "Host IP",
            "format": vcenter
        },
        {
            "header": "Port",
            "format": vcenter
        },
        {
            "header": "Vulnerability",
            "format": vcenter
        },
        {
            "header": "Severity",
            "format": vcenter
        },
        {
            "header": "CVE",
            "format": workbook.add_format(
                {
                    "text_wrap": 1,
                    "valign": "top"
                }
            )
        },
        {
            "header": "Information",
            "format": vcenter
        }
    ]

    for values in data["scanResult"]:
        for vulnerability in values["vulnerabilities"]:
            if vulnerability["id"] in vulnerabilities.keys():
                table_data.append(
                    [
                        values["ip"],
                        int(values["port"]),
                        vulnerabilities[vulnerability["id"]]["name"],
                        vulnerability["severity"],
                        # avoid to raise KeyError exceptions for entries with
                        # no CVE defined
                        # replace space with Windows' return line to prevent
                        # super wide cells
                        vulnerability.get("cve", "N/A").replace(" ", "\r\n"),
                        vulnerability["finding"]
                    ]
                )

    worksheet = workbook.add_worksheet("Host vs Vulnerability")
    draw_table(worksheet, table_headers, table_data)

def parse_host_ciphers(workbook, data):
    table_data = []
    table_headers = [
        {"header": "Host IP"},
        {"header": "Port"}
    ]

    for values in ciphers.values():
        table_headers.append({"header": values["name"]})

    for values in data["scanResult"]:
        d = {
            "Host IP": values["ip"],
            "Port": int(values["port"])
        }

        for cipher in values["ciphers"]:
            if cipher["id"] in ciphers.keys():
                d[cipher["id"]] = {
                    "name": ciphers[cipher["id"]]["name"],
                    "severity": cipher["finding"],
                }

        table_data.append(insert([x["header"] for x in table_headers], d))

    worksheet = workbook.add_worksheet("Host vs Ciphers")
    draw_table(worksheet, table_headers, table_data)

def parse_host_cipherTests(workbook, data):
    table_data = []
    table_headers = [
        {"header": "Host IP"},
        {"header": "Port"}
    ]
    header_name = "Support of weak ciphers with < %d bits" % min_acceptable_cipher_bits
    table_headers.append({"header": header_name})

    for values in data["scanResult"]:
        d = {
            "Host IP": values["ip"],
            "Port": int(values["port"])
        }

        for cipher in values["cipherTests"]:
                d[cipher["id"]] = {
                    "name": header_name,
                    "severity": cipher["finding"],
                }

        table_data.append(insert2([x["header"] for x in table_headers], d, min_acceptable_cipher_bits))

    worksheet = workbook.add_worksheet("Host vs CipherTests")
    draw_table(worksheet, table_headers, table_data)

def parse_host_vulnerabilities(workbook, data):
    table_data = []
    table_headers = [
        {"header": "Host IP"},
        {"header": "Port"}
    ]

    for values in vulnerabilities.values():
        table_headers.append({"header": values["name"]})

    for values in data["scanResult"]:
        d = {
            "Host IP": values["ip"],
            "Port": int(values["port"])
        }

        for vulnerability in values["vulnerabilities"]:
            if vulnerability["id"] in vulnerabilities.keys():
                d[vulnerability["id"]] = {
                    "name": vulnerabilities[vulnerability["id"]]["name"],
                    "severity": vulnerability["severity"]
                }

        table_data.append(insert([x["header"] for x in table_headers], d))

    worksheet = workbook.add_worksheet("Host vs Vulnerabilities")
    draw_table(worksheet, table_headers, table_data)


def main():
    try:
        args = parse_args()

        logging.addLevelName(RESULT, "RESULT")
        logging.basicConfig(
            format="%(levelname)-8s %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout)
            ],
            level=args.loglevel
        )

        if args.output_file:
            output_file = "{}.xlsx".format(args.output_file)
        else:
            output_file = "testssl-results_{}.xlsx".format(
                time.strftime("%Y%m%d-%H%M%S")
            )

        # variables summary
        logging.info("pretty JSON input file: {}".format(args.input_file.name))
        logging.info("XLSX output file: {}".format(output_file))
        logging.info("certificate issue(s) to process: {}".format(
            sorted(certificates.keys())
        ))
        logging.info("protocol(s) to process: {}".format(protocols))
        logging.info("vulnerability/ies to process: {}".format(
            sorted(vulnerabilities.keys())
        ))

        data = json.load(args.input_file)

        workbook = xlsxwriter.Workbook("{}".format(output_file))

        logging.log(
            RESULT,
            "generating worksheet 'Host vs Certificate'..."
        )
        parse_host_certificate(workbook, data)

        logging.log(
            RESULT,
            "generating worksheet 'Host vs Certificates'..."
        )
        parse_host_certificates(workbook, data)

        logging.log(
            RESULT,
            "generating worksheet 'Host vs Protocol'..."
        )
        parse_host_protocol(workbook, data)

        logging.log(
            RESULT,
            "generating worksheet 'Host vs Protocols'..."
        )
        parse_host_protocols(workbook, data)

        logging.log(
            RESULT,
            "generating worksheet 'Host vs Vulnerability'..."
        )
        parse_host_vulnerability(workbook, data)

        logging.log(
            RESULT,
            "generating worksheet 'Host vs Vulnerabilities'..."
        )
        parse_host_vulnerabilities(workbook, data)

        logging.log(
            RESULT,
            "generating worksheet 'Host vs Ciphers'..."
        )
        parse_host_ciphers(workbook, data)

        logging.log(
            RESULT,
            "generating worksheet 'Host vs CipherTests'..."
        )
        parse_host_cipherTests(workbook, data)

        workbook.close()
    except KeyboardInterrupt:
        logging.exception("'CTRL+C' pressed, exiting...")


if __name__ == "__main__":
    main()
