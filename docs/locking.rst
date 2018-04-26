################
Resource Locking
################

********
Overview
********
A key requirement of any automated data processing pipeline is an effective locking strategy to ensure that:

* multiple processes do not write to the same data resource
* data resources are not updated whilst being actively consumed

Whilst there are implementation-specific locking technologies on the database level, this project takes a "soft" lock approach where different processes register that they are either reading from or writing to a named resource.

******
Design
******
Lock state is stored persistently in a simple relational schema, shown below:

.. image:: ./resource_lock_schema.png

A lock is created as a row in `resource_lock` for a given combination of client, resource and lock type. A `client` is uniquely identified by a name (this is intended to be an identifier for the process or person) and a `resource` is uniquely identified by a URI e.g. a database URI.

Any number of read locks can be created on a given resource, unless an existing write lock is present

Write locks can only be created if there are no locks (read or write) for the resource. Note that locks are not reentrant though this would be a simple change to make if it were deemed safe.

To allow concurrent processes to request and obtain locks safely, locking and unlocking calls are made by transactions which lock the tables used. A resource is locked by inserting a row in `resource_lock` and unlocked by removing that row.


**************
Implementation
**************
The current python implementation from `ensembl_prodinf/resource_lock.py` uses SQLAlchemy as an abstraction over MySQL. The main classes are:

* ``Client`` - simple class encapsulating a client and corresponding to a row in the ``client`` table
* ``Resource`` - simple class encapsulating a resource and corresponding to a row in the ``resource`` table
* ``ResourceLock`` - class encapsulating an instance of ``Client``, an instance of ``Resource``, a lock type (``read`` or ``write``) and a timestamp, corresponding to a row in the ``resource_lock`` table
* ``ResourceLocker`` - methods for creating and retrieving ``Client`` and ``Resource`` objects and for locking and unlocking

Full documentation can be found in the classes but basic usage:

.. code-block:: python

   locker = ResourceLocker('mysql://user:pass@host:3306/resource_lock')
   # obtain a read lock
   my_lock = locker.lock('my_client_name', 'uri://my_resource', 'read')
   # ...do some stuff
   # release the lock
   locker.unlock(lock)
   # retrieve all active locks
   for lock in locker.get_locks():
     print lock
    
Note that the database ``resource_lock`` must exist, but will be automatically populated if empty.

If a resource cannot be locked, a ``LockException`` is raised.

Unit tests can be found in ``tests/test_locking.py``
