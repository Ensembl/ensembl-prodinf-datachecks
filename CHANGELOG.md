CHANGELOG - Ensembl Prodinf Database copy
=========================================

v2.0.1
------
- BugFix incomplete DC status for failed dc jobs


V2.0.0
------
- Deployed DC App to k8s 

v1.2.1
------

- BugFIX on js for datachecks listing.
- Added App version in menu header

v1.2.0
------

- Enable apps to work with an APP prefix (metazoa/datachecks for instance), to tun behind nginx proxy.
- Remotely load config on startup to enable loading list of available datachecks from remote `ensembl-datacheck`
  repository
- Added unit test for new features.

v1.1.0
----

- Integrates DC Status updates to display DC c% of completion

v1.0.0
------

- Initial Refactor 1.0.0
