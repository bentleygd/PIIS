from os.path import join, exists
from os import walk
from logging import getLogger
from re import search, compile
from configparser import ConfigParser
from hashlib import sha256

from openpyxl import load_workbook


class GetFileList:
    """Non-data descriptor for recursively enumerating files in several
    directories."""

    def __get__(self, obj, objtype=None):
        """Enumerates files in the specified directories.

        Required Input:
        scan_dirs - list(), The directories to recursively enumerate.

        Output:
        file_list - list(), A list of files in a directory.

        Exceptions:
        OSError - Occurs if the directory does not exist.
        PermissionError - Occurs if there are permissions problems."""
        log = getLogger(__name__)
        config = ConfigParser()
        config.read('example.ini')
        scan_dirs = config['targets']['scan_dir'].split(',')
        file_list = []
        # Checking to see if the directory exists.
        for _dir in scan_dirs:
            try:
                if not exists(_dir):
                    raise OSError
            except OSError:
                log.error('Specified directory does not exist')
            # Since it exists, recursively enumerate all files.
            try:
                for root, dirs, files in walk(_dir):
                    for name in files:
                        file_list.append(join(root, name))
            except PermissionError:
                log.error(
                    'Permission error when enumerating the files in %s' % _dir
                )
        return file_list


class PIIScanner:
    """A PII scanning object.

    Class Variables:
    file_list - list(), The returned list of files from the GetFilelist
    non-data descriptor.

    Methods:
    ssn_scan_file - Scans a flat file for SSNs.
    ssn_scan_excel - Scans an Excel spreadsheet for SSNs.
    hash_ssn - Generates a sha256 hash for SSNs.
    """
    file_list = GetFileList()

    def __init__(self):
        """Creates a PIIScanner object.

        Instance variables:
        log - A logger object.
        ssn - A regex expression object for SSNs.
        ssn_hashes - list(), A list of unique SSN hashes.
        ssn_files - list(), A list of flat files containing SSNs.
        ssn_excel - list(), A list of Excel spreadsheets containing SSNs."""
        self.log = getLogger(__name__)
        self.ssn = compile(
            r'\b\d{9}\b|\d{3}\-\d{2}\-\d{4}|\d{3}\s\d{2}\s\d{4}'
        )
        self.ssn_hashes = []
        self.ssn_files = []
        self.ssn_excel = []

    def hash_ssn(self, ssn):
        """Converts a matched SSN to a 9 digit string and then creates
        a sha256 hash of that value.

        Required Input:
        ssn - str(), A United States Social Security number.

        Returns:
        hashed_value - str(), The hex digest of the sha256 hash of the
        SSN."""
        if '-' in ssn:
            converted_ssn = ssn.replace('-', '')
            hashed_value = sha256(converted_ssn.encode()).hexdigest()
            return hashed_value
        elif ' ' in ssn:
            converted_ssn = ssn.replace(' ', '')
            hashed_value = sha256(converted_ssn.encode()).hexdigest()
            return hashed_value
        else:
            hashed_value = sha256(ssn.encode()).hexdigest()
            return hashed_value

    def ssn_scan_file(self, file_path):
        """Scans a file for the specified pattern, returns True if found.

        Required Inputs:
        file_path - str(), A file-like object to scan for patterns.

        Output:
        scan_result - Bool(), True or False depending on the presence
        of the pattern.

        Exceptions:
        None."""
        # Looking for SSNs in each line of the file-like object.
        try:
            file_object = open(file_path, 'r')
        except PermissionError:
            self.log.error(
                'Unable to open %s due to permission error' % file_path
            )
        for line in file_object:
            search_result = search(self.ssn, line)
            # If a SSN is found, log it.  If a file contains more than
            # one SSN, increment the counter by one but only log that
            # the file has one SSN.
            if search_result:
                scan_result = True
                # Hash the SSN and check to see if it's been detected
                # yet.  If it hasn't, add it to the list of unique ssn
                # hashes.
                ssn_hash = self.hash_ssn(search_result.group(0))
                if ssn_hash not in self.ssn_hashes:
                    self.ssn_hashes.append(ssn_hash)
                ssn_file_names = [
                    _file['name'] for _file in self.ssn_files
                    ]
                if file_object.name not in ssn_file_names:
                    self.log.info(
                        'SSN detected in ', file_object.name
                        )
                    self.ssn_files.append({
                        'name': file_object.name,
                        'count': 1})
                else:
                    for ssn_file in self.ssn_files:
                        if ssn_file['name'] == file_object.name:
                            ssn_file['count'] += 1
            else:
                # The lack of SSNs is not enough reason to log as info
                # as this should be the expected outcome.
                scan_result = False
                self.log.debug('No SSNs found in ', file_object.name)
        file_object.close()
        return scan_result

    def ssn_scan_excel(self, path):
        """Scans an Excel work book for SSNs, returns true if any are found.

        Required Input:
        path - str(), The location of an Excel workbook.

        Output:
        scan_result - Bool(), True or False depending on the presence
        of the pattern.

        Exceptions:
        OSError - Occurs when unable to open the specified workbook."""
        try:
            wb = load_workbook(path)
        except PermissionError:
            self.log.error(
                'Unable to open %s due to permission error.' % path
            )
        except Exception:
            self.log.exception('Unable to open ', path)
        # Iterating through each sheet in a workbook.
        for sheet in wb:
            # Iterating through the rows of the worksheet.
            for row in sheet.values:
                # Iterating through all the values of a row, checking if
                # there is a SSN.  If a SSN is found, log it and add the
                # file name to the instance variable of Excel sheets that
                # contain SSNs.  If a spreadsheet has more than one SSN,
                # then increment the count by one for that spreadsheet.
                for value in row:
                    search_result = search(self.ssn, str(value))
                    if search_result:
                        scan_result = True
                        # Hash the SSN and check to see if it's been
                        # detected yet.  If it hasn't, add it to the
                        # list of unique ssn hashes.
                        ssn_hash = self.hash_ssn(search_result.group(0))
                        if ssn_hash not in self.ssn_hashes:
                            self.ssn_hashes.append(ssn_hash)
                        excel_file_names = [
                            _file['name'] for _file in self.ssn_excel
                            ]
                        if path not in excel_file_names:
                            self.log.info(
                                'SSN detected in %s:%s' % (path, sheet.title)
                            )
                            self.ssn_excel.append({
                                'name': path,
                                'count': 1
                            })
                        else:
                            for excel_sheet in self.ssn_excel:
                                if excel_sheet['name'] == path:
                                    excel_sheet['count'] += 1
                    else:
                        scan_result = False
                        self.log.debug(
                            'No SSNs found in %s:%s' % (path, sheet.title)
                        )
        wb.close()
        return scan_result
