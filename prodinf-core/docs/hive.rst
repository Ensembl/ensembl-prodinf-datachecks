*****************
eHive Integration
*****************

Overview
########

The `ensembl_prodinf.hive` package contains utilities for interacting with an eHive database. This includes:

* submitting new jobs
* checking on the status of individual jobs
* checking on the status of job hierarchies using semaphores
* retrieving results from custom result tables
* retrieving log message for parent and children jobs

The package uses the SQL Alchemy ORM package for creating and retrieving jobs from a hive database, with custom code for checking on semaphores and job hierarchies.

Data model
##########

Selected tables from the eHive schema are mapped to Python objects using SQL Alchemy. The objects used are:

* Job - central object representing a job that has been submitted.
* Analysis - analysis to which a job belongs
* AnalysisData - additional data for that analysis
* Result - output from a job hierarchy. Note that this uses a non-standard
* JobProgress - allows progress of an individual job to be tracked
* LogMessage - messages associated with a job
* Role - role needed for a job, which is used to associate a worker with a job
* Worker - worker running a job. Needed to kill a job.

These objects are used by the other methods in HiveInstance.

Note that jobs frequently represent factory jobs which then generate entire hierarchies controlled by semaphores. In this case, results represent collated, and status is detected from semaphores.

Compatible eHives
#################

The basic code can be used with any eHive schema, but use of the `Result` object assumes that the result from a job or job hierarchy ends up in a result table named `output`.

In addition, there should also be a `job_progress` table to allow use of the `JobProgress` table.

Lastly, some usage scenarios involve inserting large input values, and submitting multiple jobs with the same input. The easiest way to support these requirements are to modify the job table to allow these actions.

These additional tables can be created by the hive pipeline config e.g.

.. code-block:: perl

  sub pipeline_create_commands {
     my ($self) = @_;
     return [
	    @{$self->SUPER::pipeline_create_commands},  # inheriting database and hive tables' creation
        # support for collation of job results
	    $self->db_cmd('CREATE TABLE result (job_id int(10), output TEXT, PRIMARY KEY (job_id))')
        # support for per-job progress tracking
        $self->db_cmd('CREATE TABLE job_progress (job_progress_id int(11) NOT NULL AUTO_INCREMENT, job_id int(11) NOT NULL , message TEXT,  PRIMARY KEY (job_progress_id))'),
        $self->db_cmd('ALTER TABLE job_progress ADD INDEX (job_id)'),
        # support for multiple jobs with same input
        $self->db_cmd('ALTER TABLE job DROP KEY input_id_stacks_analysis'),
        # support for large inputs
        $self->db_cmd('ALTER TABLE job MODIFY input_id TEXT')
    ];
  }


For an example, see the `tests/perl` directory for the `TestPipeline_conf` pipeline. Basic usage is shown in `tests/test_hive.py`

The hive code assumes that the hive database has been initialized and the beekeeper is running.

Usage
#####

The central object is HiveInstance, which is instantiated with a URL to a pre-existing Hive database. Jobs can then be created by passing in the analysis name and a dict containing the job input:

.. code-block:: python

   hive = HiveInstance("sqlite:///"+dirpath+"/test_pipeline.db")
   job1 = hive.create_job('TestRunnable',{'x':'y','a':'b'})

If a beekeeper is running against that hive, then it will be processed as normal.

Jobs can be retrieved by ID and the status of the job or its semaphores can be checked:

.. code-block:: python

   job1 = hive.get_job_by_id(1)
   status = hive.check_semaphores_for_job(job1)
   output = hive.get_result_for_job_id(1)


