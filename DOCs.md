# PIIS Documentation

<h2>PIIS Functions</h2>

<h3>get_file_list(scan_dir) </h3>
This function utilizes the os.path.walk() function to enumerate all files under a specified directory and returns the results as a list of files to scan.

**Required Input**
- scan_dir \- A string representing the directory to enumerate.  Please note that the enumeration is recursive.

**Output**
- file_list \- A list containg each file (with the full path) discovered during the enumeration process.

**Exceptions**
- OSError \- Occurs if there is a problem with accessing the directory.

Code Example:
```python
from pii_scan import get_file_list
from os import stat


file_list = get_file_list('/opt/example_dir')
file_info = []
for file in file_list:
    data = {
        'file_name': file,
        'stat_info': stat(file)
        }
    file_info.append(data)
```
