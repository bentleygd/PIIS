from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
from logging import getLogger, basicConfig, INFO
from time import time
from csv import DictWriter

from libs.pii_scan import PIIScanner


def main():
    # Setting up and starting logging.
    log = getLogger(__name__)
    basicConfig(
        filename='pii_scan.log',
        format='%(asctime)s %(name)s %(levelname)s: %(message)s',
        datefmt='%m/%d/%Y %H:%M:%S',
        level=INFO
    )
    # Getting config.
    config = ConfigParser()
    config.read('example.ini')
    # Getting variables from config file.
    thread_count = int(config['core']['thred_count'])
    # Instantiating PII Scanner
    scanner = PIIScanner()
    file_list = scanner.file_list
    # Scanning files for SSNs.
    log.info('%d files will be scanned.' % len(file_list))
    log.info('Starting SSN file scan.')
    start = time()
    # Note that the thread count is set in the configuration.
    log.debug('Scanning with %d threads' % thread_count)
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        try:
            for _file in file_list:
                # Checking for file extension in order to execute the
                # appropriate PII scan method.
                if str(_file).endswith(('xlsx', 'xls')):
                    log.debug('Scanning %s for SSNs' % _file)
                    executor.submit(scanner.ssn_scan_excel, _file)
                elif str(_file).endswith(('pgp', 'gpg')):
                    log.debug('Skipping over %s' % _file)
                    pass
                else:
                    log.debug('Scanning %s for SSNs' % _file)
                    executor.submit(scanner.ssn_scan_file, _file)
        except PermissionError:
            log.error('Permission error when scanning %s' % _file)
    finished = time()
    elapsed = finished - start
    # Logging completed scan info.
    log.debug('Scan completed in %r seconds' % elapsed)
    log.info('Scan for SSNs completed.')
    total_files = len(scanner.ssn_excel) + len(scanner.ssn_files)
    log.info('%d files contianed SSNs' % total_files)
    log.info('%d unique SSNs were discovered.' % len(scanner.ssn_hashes))
    # Generating CSV Summary Report
    csv_fields = ['file_name', 'ssn_count']
    results_file = open('PIIS_summary.csv', 'w+')
    writer = DictWriter(results_file, fieldnames=csv_fields)
    writer.writeheader()
    for ssn_file in scanner.ssn_files:
        writer.writerow({
            'file_name': ssn_file['name'],
            'ssn_count': ssn_file['count']
        })
    for ssn_excel in scanner.ssn_excel:
        writer.writerow({
            'file_name': ssn_excel['name'],
            'ssn_count': ssn_excel['count']
        })
    results_file.close()


if __name__ == '__main__':
    main()
