
# SMART Diabetes Logbook: Clinican App

Arjun Sanyal <arjun.sanyal@childrens.harvard.edu>

See the SMART Diabetes Logbook: Patient App README for an overview of
the "merge" app concept and complete details of both the patient and
clinican facing apps.

---

This is the clinican-facing side of the SMART Diabetes Logbook pair of
apps. It implements a simple SMART REST app that establishes a
connection between a patient record in a SMART container and a patient
record in Microsoft HealthVault using the HealthVault [Patient
Connect][] API. Each connection request is stored in a persisent SQLite
database and is later updated with the HealthVault patient and record
ids by a polling script.

Once the connection is established it shows a set of patient-reported
data from the HealthVault record and clinical data from the SMART
record in one combined interface.

[Patient Connect](http://msdn.microsoft.com/en-us/library/jj551258.aspx)


## TODO

- Create a second "mappings" table and don't overload requests


## Requirements
  
- Python 2.7 or above
- SQLite3

- Python Modules
  - flask
  - lxml
  - pycrypto
  - rdflib
  - rdfextras


## Setup and Running

- After cloning do: `git submodule update --init --recursive`
- To setup: `python setup.py` to create the SQLite3 request database in `/data`
- To run on port 8000: `python wsgi.py`
- Then log in to the SMART container e.g. <http://sandbox.smartplatforms.org>
- Launch the "My App" app, which will point at your locally
  hosted version of this app running on port 8000
