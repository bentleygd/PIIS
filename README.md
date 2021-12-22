# PIIS
Python scripts used to search for PII data in files.

# Purpose
This project was started to provide the capability to quickly discover where files containing PII data may reside in order to create an accurate data inventory of sesnitive data locations.

- Supports United States Social Security Number discovery.

# Install

Add later.

# Usage
In order to run the user security review scripts, run:  
`$ python3 pii_scan.py`  

# Documentation
See DOCS.md for more detailed documentation.

# Features
- Automated file scanning for PII data.
<h2>Social Security Numbers</h2>
Support for scanning for Social Security Numbers (SSNs) is supported for standard files and for Microsoft Office Excel workbooks (including support for multiple worksheets).

# Testing
Automated unit tests are included and use the pytest framework.  Executing the tests is simple:  
`$ python3 -m pytest -v`

# License
This project is licensed under GPLv3.
