
SMART Microsoft HealthVault Merge App
--------------------------------------

Arjun Sanyal <arjun.sanyal@childrens.harvard.edu>

Implements a simple SMART REST app that establishes a connection to a user
using the HealthVault [Patient Connect][] API. Each request is stored in a
persisent SQLite database and is later updated with the HealthVault patient
and record ids by a script that polls HealthVault for authorized requests. The
script is run manually, but could be automated.

Once the connection is established it shows a set of patient-reported data
(weights) and clinical data from the SMART Container in one interface.

[Patient Connect](http://msdn.microsoft.com/en-us/library/jj551258.aspx)

* Requirements
  * Python 2.7 or above
  * `web.py`

* To run `python merge.py 8000`
* Then log in to the reference container: <http://sandbox.smartplatforms.org>
* Launch the "Developers Sandbox" app, which will point at your locally
  hosted version of this app
