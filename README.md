# DRACOON-PYTHON-API

. 
- DRACOON object and call handlers in core.py
- Route specific reequests in individual modules (e.g. users, nodes)



  <h3 align="center">DRACOON-PYTHON-API</h3>

  <p align="center">
    Python connector to DRACOON API
    <br />
    <a href="https://github.com/unbekanntes-pferd/DRACOON-PYTHON-API"><strong>Explore the docs »</strong></a>
    <br />
    <a href="hhttps://github.com/unbekanntes-pferd/DRACOON-PYTHON-API/issues">Report Bug</a>
    ·
    <a href="https://github.com/unbekanntes-pferd/DRACOON-PYTHON-API/issues">Request Feature</a>
  </p>
</p>



<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About the Project](#about-the-project)
  * [Built With](#built-with)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
* [Usage](#usage)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)
* [Contact](#contact)
* [Acknowledgements](#acknowledgements)



<!-- ABOUT THE PROJECT -->
## About The Project
_Disclaimer: this is an unofficial repo and is not supported by DRACOON_
This package provides a connector to DRACOON API. 
DRACOON is a cloud storage product / service (SaaS) by DRACOON GmbH (http://dracoon.com). 
DRACOON API documentation can be found here (Swagger UI):
https://dracoon.team/api/


### Built With

* [Python 3.7.3](https://www.python.org/)
* [Python requests](https://requests.readthedocs.io/en/master/)

<!-- GETTING STARTED -->
## Getting Started

To get started, create a virtual environment in Python and install the dracoon package:
```
virtualenv <DIR>
source <DIR>/bin/activate 
python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps dracoon-UNBEKANNTES-PFERD
```

### Prerequisites

You will need a working Python 3 installation - check your version:
* Python
```
python3 --version
```

### Installation

1. Install the package from TestPyPi
```
python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps dracoon-UNBEKANNTES-PFERD
```

Please note: this package will also be provided via official PyPi soon.

<!-- USAGE EXAMPLES -->
## Usage
* Import required modules
```
from dracoon import core, users
```

Modules are named after API endpoints (see documentation for further details).
_Exception: core module - this is required to create Dracoon object and to send authenticated requests to the API._

* Object creation
```
my_dracoon = core.Dracoon(clientID, clientSecret)
```
Please note: providing a client secret is optional (in order to use with OAuth apps that don't have one).


* Authentication
```
login_response = my_dracoon.basic_auth(username, password)
```
Please note: you can only authenticate if OAuth app is correctly configured. Only local accounts can be used via password flow.

* Send requests

1. First you will need to build a request with specific parameters:
```
r = users.get_users(offset=0, filter=f)
```

Please note: 
* GET requests are limited to returning 500 items. Therefore all such requests contain an offset parameter (default is 0)
* Providing a filter is optional - see API documentation and examples on usage
* Sorting not implemented - sorting results should occur via client

2. you can then send the request as an authenticated user
```
user_response = my_dracoon.get(r)
```
Supported request types:
* GET (object.get(request))
* POST (oject.post(request))
* PUT (object.put(reqest))
* DELETE (object.delete(request))

_For examples, check out the example files:_

* [DRACOON authentication](/authentication_example.py)
* [Export user list to CSV](/user_csv_example.py)


<!-- ROADMAP -->
## Roadmap

* Implement public API to upload files 
* Implement missing API endpoint (selection)
    * shares
    * eventlog 
    * uploads
    * public
* Distribute package via official PyPi

<!-- LICENSE -->
## License

Distributed under the Apache License. See [LICENSE](/LICENSE) for more information.
