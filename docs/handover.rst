###################
Handover Processing
###################

********
Overview
********
Handover processing deals with bringing a new database from an upstream data team onto staging. It covers the following main steps:

* Check the database exists and passes integrity checks
* Copies the database to staging
* Records the new database in the metadata store
* Triggers any required processing (e.g. dumping new files)

*****
Logic
*****
The sequence of logical steps of receiving is as follows:

#. Check specification of source and target databases and event details are correct
#. Check that source database exists
#. Submit source database to `healthcheck service <https://github.com/Ensembl/ensembl-prodinf-srv/blob/master/README_hc.rst>`_
#. Wait for healthchecks to be completed and abort (with an email report) if it does not pass
#. Submit source database to `copy service REST endpoint <https://github.com/Ensembl/ensembl-prodinf-srv/blob/master/README_db.rst>`_ for copying to staging
#. Wait for copy to complete and abort (with an email report) if it does not pass
#. Submit newly updated database to `metadata service REST endpoint <https://github.com/Ensembl/ensembl-prodinf-srv/blob/master/README_metadata.rst>`_
#. Wait for metadata update to complete and receive event from service
#. Pass event to `event handling <./event_handling.rst>`_ endpoint for further processing

This is summarised in the following diagram:

.. image:: handover_endpoint_logic.png

**********
Components
**********

Handover endpoint
=================
The main entry point for submitting databases for handover is the `handover REST endpoint <https://github.com/Ensembl/ensembl-prodinf-srv/blob/master/README_handover.rst>`_. Code for this can be found in the `ensembl-prodinf-srv <https://github.com/Ensembl/ensembl-prodinf-srv>`_ repository.

This endpoint has a single method, ``submit`` which accepts a specification containing:

* ``src_uri`` - URI to database to handover (required)
* ``tgt_uri`` - URI to copy database to (optional - generated from staging and src_uri if not set)
* ``contact`` - email address of submitter (required)
* ``type`` - string describing type of update (required)
* ``comment`` - additional information about submission (required)

The endpoint delegates processing to ``ensembl_prodinf.handover_tasks.handover_database`` which carries out some basic checking and then submits a healthcheck job and creates a celery task for checking on the status of the healthcheck and triggering the next step. 

This method returns a unique endpoint token which is also used by the reporting endpoint so that progress of a handover can be tracked.

Reporting
=========
Reporting uses the queue-based mechanism found in `ensembl-prodinf-report <https://github.com/Ensembl/ensembl-prodinf-report>`_ fronted by an instance of Python logging.
 
Celery tasks
============
A sequence of celery tasks is used to trigger and then wait for each step in the process, and then trigger further tasks as required.

The tasks are defined in `ensembl_prodinf.handover_tasks <../ensembl_prodinf/handover_tasks.py>`_ and follow a standard pattern of waiting for completion by checking for completion of a submitted job using the standard ensembl_prodinf hive-based endpoints. This wait is implemented as the task checking for completion and then raising a retry exception, which then allows the celery worker to retry an infinite number of times until the job succeeds or fails.

The sequence is triggered by ``ensembl_prodinf.handover_tasks.handover_database`` which submits a healthcheck job and then creates a ``process_checked_db`` task. The tasks are:

* ``process_checked_db`` - waits for a healthcheck job to complete, and then either emails the submitter if there are failures, or if successful submits a copy job and a ``process_copied_db`` task
* ``process_copied_db`` - waits for the specified copy job to complete, and then submits a metadata update job and creates a ``process_db_metadata`` task. 
* ``process_db_metadata`` - waits for the specified metadata update job to complete, and then submits the event returned by the metadata endpoint to the event processing endpoint.

Handover web interface
======================
The handover web page created for use by the metadata service can be reused for submission to the handover endpoint.