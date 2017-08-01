*****************
eHive Integration
*****************

Overview
########

The `ensembl_prodinf.hive` package contains utilities for interacting with an eHive database. This includes:
* submitting new jobs
* checking on the status of individual jobs
* checking on the status of job hierarchies
* retrieving results from custom result tables

The package uses the SQL Alchemy ORM package for creating and retrieving jobs from a hive database, with custom code for checking on semaphores and job hierarchies.

The central object is HiveInstance, which is instantiated with a URL to the Hive database e.g.

::
   hive = HiveInstance("sqlite:///"+dirpath+"/test_pipeline.db")
   job1 = self.hive.create_job('TestRunnable',{'x':'y','a':'b'})

Compatible eHives
#################

The basic code can be used with any eHive schema, but use of the `Result` object assumes that the result from a job or job hierarchy ends up in a result table named `output` with the following columns:
* job_id - ID of the input job (which may be the factory job that fires off a hierarchy)
* output - serialized result in JSON format

Note that the hive code assumes that the hive database has been initialized and the beekeeper is running.

For an example, see the `tests/perl` directory for the `TestPipeline_conf` pipeline. Basic usage is shown in `tests/test_hive.py`

