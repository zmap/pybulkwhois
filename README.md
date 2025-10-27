# Python Bulk WHOIS

This is a Python library that allows interacting with the bulk WHOIS data that
RIRs (e.g., RIPE, ARIN, AFRINIC) provide about the ownership of ASes and netblocks.

0. One-time environment setup, from the top-level directory

```shell
python3 -m venv venv;
source venv/bin/activate;
pip install -r requirements.txt
```

Ensure you've created a `logins.json` in the top-level directory with your RIR credentials of the form:

```json
{
    "LACNIC_UID": "ABC",
    "LACNIC_PWD": "123",
    "APNIC_UID": "ABC",
    "APNIC_PWD": "123",
    "ARIN_UID": "ABC",
    "ARIN_PWD": "123"
}
```

1. Run from top level directory using:

> python -m pybulkwhois.makeases

## License and Copyright

PyBulkWHOIS Copyright 2018 Regents of the University of Michigan

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See LICENSE for the specific
language governing permissions and limitations under the License.
