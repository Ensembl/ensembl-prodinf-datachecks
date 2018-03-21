################
Event Processing
################

********
Overview
********
The event processing infrastructure supports the execution of automated pipelines in response to known events on the staging server. For instance, the introduction of a new assembly into staging could trigger pipelines to dump new DNA and new peptide files. In this context, events are those used by the metadata service/database to record the history of a given database.

In addition, the event infrastructure may also generate further events for processing - for instance, a new genebuild might trigger the protein feature pipeline, which in turn requires flatfile dumps to be run. Note that the complexity of the Ensembl release process may require additional logic to defer the execution of processes until all expected events that might trigger it have completed. For instance, flatfile dumping could be triggered by both a new genebuild and new cross-references, but should not be executed twice on the same new genebuild which is then updated for xrefs.

*****
Logic
*****
The event processing service carries out the following steps
#. Accepts a new event specification from a client. This might include a genome or other resource identifier, an update type and comments/parameters.
#. Determines which processes correspond to that trigger
#. Submits a process job for each of the corresponding processes
#. Waits for the completion of each job
#. Records any events that have been generated

This is summarised in the following diagram:
.. image event_handling_logic.png

**********
Components
**********

Event endpoint
==============
The main entrypoint for the event processing service is the event flask app which exposes the `/jobs` endpoint for the creation, deletion and polling of event processing jobs.

When a new event is POSTed to `/jobs`, the event type is used to consult `event_lookup.json` to find which processes are associated with that type. Each process is then used to consult `process_lookup.json` to find which hive instances and analysis types are needed to run a process of that type. For instance, `new_assembly` events are linked to `dump_dna` and `dump_peptide` processes, and these processes are then executed by the submission of new jobs to the hives associated with those processes.

In contrast to the healthcheck and copy endpoints, job submission returns an array of items containing a process and a job ID, since job ID is only unique to a given process hive. These are then used in all subsequent endpoint interactions such as result retrieval e.g. submitting a `new_genebuild` event might return `dump_peptide` job 1, which can then be checked using `/jobs/dump_peptide/1`.

Hive pipelines
==============
The endpoint is capable of submitting jobs to any hive pipeline that meets the standard criteria for seeding jobs and waiting for results, and multiple different processes can be run in the same hive or different hives, depending on load etc.

An example is shown in `Bio::EnsEMBL::Production::Pipeline::EventHandling::EventHandling_conf`. In this example, the entry point for job seeding is `Bio::EnsEMBL::Production::Pipeline::EventHandling::EventHandler` which accepts an event object and then seeds new jobs as appropriate. In this example, there are multiple analyses of this class, but it would be equally valid to have a single analysis which then flows events to different branches according to the event.

Dumping is then handled by standard hive analyses from the existing FTP pipeline, and completion is monitored via a semaphored job of class `Bio::EnsEMBL::Production::Pipeline::EventHandling::EventHandlerCompletion` which writes a row to the `results` table which can be checked by the controlling task. This does not contain anything beyond indicating success.

Reporting
=========
Reporting is carried out using the queue-backed Python and Perl implementations used elsewhere.

Celery tasks
============
Once each process for an event is submitted, a `process_result` task from `ensembl_prodinf.event_tasks` is submitted. This periodically polls the hive for success, and is intended to update the metadata database and submit new events as required (this is not yet implemented).

Client
======
A simple client intended for command line and programmatic use is provided in `ensembl_prodinf.EventClient`. This provides basic support for event submission and job polling.

Event processing web interface
==============================
Currently it is difficult to determine whether an event processing interface is needed as this is intended to work completely automatically. However, manual scheduling of events in response to external factors (e.g. a new release of interproscan) might be needed in future.
