Installation
============

To install Python requirements using pip:
```
pip install -r requirements.txt
```
You can also install `ensembl_prodinf` from git or by adding an existing install to PYTHONPATH.

Hive Setup
==========

Before you can use the HC endpoint, you need a beekeeper running the pipeline defined by `Bio::EnsEMBL::Production::Pipeline::PipeConfig::CopyDatabase_conf`. To build and initiate the pipeline:
```
git clone https://github.com/Ensembl/ensembl-production
cd ensembl-production
SRV=your_mysql_command_wrapper from where your hive will be running.
init_pipeline.pl Bio::EnsEMBL::Production::Pipeline::PipeConfig::CopyDatabase_conf $($SRV details hive)
```

Next, run the `beekeeper.pl` supplied by the output with the arguments `--keep_alive -sleep 0.2`. This ensures the hive runs continually, picking up new jobs as they are submitted.

Configuration
=============

There is one configuration files you need to have copies of locally:
```
mkdir instance
cp db_config.py.instance_example instance/db_config.py
```

Edit them as required. db_config.py must contain a dict containing lists of server names for autocomplete e.g.
```
SERVER_URIS = {
    "user1":[
        "mysql://user1@server1:3306/",
        "mysql://user1@server2:3306/"
    ],
    "user2":[
        "mysql://user2@server1:3306/"
    ]
}
HIVE_URI='mysql://myuser:mypass@myhost:3306/standalone_hc_hive'
```


Running
=======
Important: for the status endpoint to work, you must run the app as a user who can ssh onto any servers you want to find the status for.

To start the main application as a standalone Flask application:
```
export FLASK_APP=db_app.py
flask run --port 5002 --host 0.0.0.0
```

Note that for production, a different deployment option should be used as the standalone flask app can only serve one request at a time.
