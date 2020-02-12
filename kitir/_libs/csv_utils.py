#! /usr/bin/env python

# Standard Imports
import csv

# kitir Imports
from kitir import *

# logging
log = logging.getLogger('kitir.utils.csv')

if not running_on_windows:
    csv.field_size_limit(sys.maxsize)  # to read large queries


def read_csv_from_string(text, return_headers=False):
    """
    reads a csv (comma separated values) string using DictReader and returns a rowdicts list
    :param text: string to parse CSV from
    :param return_headers: return value becomes (rows, headers)
    :return: rows read from csv
    """
    log.trace('reading csv string: content[:20]={} len={}'.format(repr(text[:20]), len(text)))
    reader = csv.DictReader(text.splitlines())
    rows = [row for row in reader]
    if return_headers:
        return rows, reader.fieldnames
    return rows


def read_tsv_from_string(text, return_headers=False):
    """
    reads a tsv (tab separated values) string using DictReader and returns a rowdicts list
    :param text: string to parse TSV from
    :param return_headers: return value becomes (rows, headers)
    :return: rows read from csv
    """
    log.trace('reading tsv string: content[:20]={} len={}'.format(repr(text[:20]), len(text)))
    reader = csv.DictReader(text.splitlines(), dialect='excel-tab')
    rows = [row for row in reader]
    if return_headers:
        return rows, reader.fieldnames
    return rows


# noinspection PyPep8Naming
class excel_space(csv.excel):
    """Describe the usual properties of Excel-generated SPACE-delimited files."""
    delimiter = ' '


# noinspection PyTypeChecker
csv.register_dialect("excel-space", excel_space)


def read_ssv_from_string(text, return_headers=False):
    """
    reads a ssv (space separated values) string using DictReader and returns a rowdicts list
    :param text: string to parse SSV from
    :param return_headers: return value becomes (rows, headers)
    :return: rows read from csv
    """
    log.trace('reading ssv string: content[:20]={} len={}'.format(repr(text[:20]), len(text)))
    reader = csv.DictReader(text.splitlines(), dialect='excel-space')
    rows = [row for row in reader]
    if return_headers:
        return rows, reader.fieldnames
    return rows


__all__ = ['read_csv_from_string', 'read_tsv_from_string', 'read_ssv_from_string']
