from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
import datetime
import logging
logging.basicConfig()

def lazy_load(obj):
    """
    Helper method to call all attribs on an obj to load them before detaching from the session
    """
    [getattr(obj, method) for method in dir(obj) if callable(getattr(obj, method))]

Base = declarative_base()

class LockEnum(Enum):
    read = 1
    write = 2    

class ResourceLock(Base):
    """Class respresenting a lock obtained by a client on a particular resource. Locks can include read or write.
    
    Attributes:
    resource_lock_id -- ID for the lock (given to the calling code for release)
    lock_type        -- read or write
    created          -- time at which lock was obtained
    client           -- Client holding the lock
    resource         -- Resource being locked
    """
    __tablename__ = 'resource_lock'

    resource_lock_id = Column(Integer, primary_key=True)
    lock_type = Column(String(5), nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    client_id = Column(Integer, ForeignKey("client.client_id"))
    client = relationship("Client")
    resource_id = Column(Integer, ForeignKey("resource.resource_id"))
    resource = relationship("Resource")
    
    def __repr__(self):
        return "<ResourceLock(resource_lock_id={}, lock_type='{}', client='{}', resource='{}')>".format(self.resource_lock_id, self.lock_type, self.client.name, self.resource.uri)

class Resource(Base):
    """Class respresenting an abstract resource like a database or a file
    
    Attributes:
    resource_id -- internal ID for the resource
    uri         -- unique string representation of the resource e.g. database URI, path to file
    """
    __tablename__ = 'resource'

    resource_id = Column(Integer, primary_key=True)
    uri = Column(String(512), nullable=False, unique=True)

    def __repr__(self):
        return "<Resource(resource_id={}, uri='{}')>".format(
            self.resource_id, self.uri)

class Client(Base):
    """Class respresenting an abstract client who needs access to a resource.
    A client might be a process, application or Real Person[tm]
    
    Attributes:
    client_id -- internal ID for the client
    name      -- unique string name for client. Could be the name of an application, or an email address for a person
    """

    __tablename__ = 'client'

    client_id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False, unique=True)

    def __repr__(self):
        return "<Client(client_id={}, name='{}')>".format(
            self.client_id, self.name)

class LockException(Exception):
    pass

Session = sessionmaker()
class ResourceLocker:

    """Utility class for the locking and unlocking of resources    
    """

    def __init__(self, url, timeout=3600):
        """Create a new ResourceLocker instance
        Attributes:
          url - URL of backing database
          timeout - (optional) time in seconds to keep connections to database open. Defaults to 3600s
        """
        self.url = url
        engine = create_engine(url, pool_recycle=timeout, echo=False)
        Base.metadata.create_all(engine)
        Session.configure(bind=engine)

    def get_client(self, name, session=None):
        """Get or create a client with the given name"""
        return self._get_object(Client, name=name, session=session)
    
    def get_resource(self, uri, session=None):
        """Get or create a resource with the given URI"""
        return self._get_object(Resource, uri=uri, session=session)

    def _get_object(self, obj_type, **kwargs):
        """Fetch or create a basic object from the database.
        If the object is not present, create it.
        If it has already been created, return it.
        If a duplicate exists, retry the method.
        """
        has_session = 'session' in kwargs
        session = kwargs.pop('session', Session())
        if session == None:
            has_session = False
            session = Session()
        try:                    
            obj = session.query(obj_type).filter_by(**kwargs).first()
            if obj:
                return obj
            else:
                obj = obj_type(**kwargs)
                session.add(obj)
                session.commit()
                # lazily load attrs so they can be accessed in a detached object
                lazy_load(obj)
                return obj
        except IntegrityError:
            # duplicate entry, so try again to fetch with a fresh session
            kwargs['session'] = session
            return self._get_object(obj_type, **kwargs)
        finally:
            if has_session == False:
                logging.debug("Closing session")
                session.close() 

    def get_locks(self, **kwargs):
        """Fetch current locks from the database
        Optional named arguments for filtering:
          id - resource_lock_id
          lock_type - read or write
          resource - URI of resource
          client - name of client
        Returns:
          List of ResourceLock objects
        """
        session = Session()                
        try:
            q = session.query(ResourceLock)
            if 'id' in kwargs:
                q = q.filter(ResourceLock.resource_lock_id == kwargs['id'])                 
            if 'lock_type' in kwargs:
                q = q.filter(ResourceLock.lock_type == kwargs['lock_type'])                 
            if 'resource' in kwargs:
                q = q.filter(Resource.uri == kwargs['resource'])
            if 'client' in kwargs:
                q = q.filter(Client.name == kwargs['client'])
            locks = q.all()
            for l in locks: lazy_load(l)
            return locks
        finally:
            session.close()
             
    def lock(self, client_name, resource_uri, lock_type):
        """Lock the specified resource.
        Arguments:
          client - name of client
          resource - URI of resource
          lock_type - read or write
        Returns:
          ResourceLock
        Raises:
          LockException if resource cannot be locked
          ValueException if lock type not read or write
        """
        logging.info("Locking {} for {} for {}", client_name, resource_uri, lock_type)
        session = Session()
        client = self.get_client(client_name, session)
        resource = self.get_resource(resource_uri, session)
        try:
            self._lock_db(session)            
            if(lock_type == 'read'):
                # can only create if no write locks found on resource
                n_locks = session.query(ResourceLock).filter_by(resource=resource, lock_type='write').count()
                if(n_locks>0):
                    raise LockException("Write lock found on {} - cannot lock for reading".format(str(n_locks), resource_uri))
                else:
                    lock = ResourceLock(resource=resource, client=client, lock_type=lock_type)
                    session.add(lock)
                    session.commit()                    
                    lazy_load(lock)
                    return lock
            elif(lock_type == 'write'):
                # can only create if no other locks found on resource
                n_locks = session.query(ResourceLock).filter_by(resource=resource).count()
                if(n_locks>0):
                    raise LockException("{} lock(s) found on {}".format(str(n_locks), resource_uri))
                else:
                    lock = ResourceLock(resource=resource, client=client, lock_type=lock_type)
                    session.add(lock)
                    session.commit()                    
                    lazy_load(lock)
                    return lock
            else:
                raise ValueError("Unsupported lock_type".format(str(lock_type)))
            self._unlock_db(session)          
        finally:            
            session.close()
        return
    
    def unlock(self, lock):
        """Release the specified lock
        Arguments:
          lock - either ResourceLock or ID of lock 
        Returns:
           None
        Raises:
          ValueError if lock not found
        """
        session = Session()
        if(type(lock) is int):
            lock = session.query(ResourceLock).filter_by(id=lock).first()
            if lock == None:
                raise ValueError("No lock found for ID "+str(lock))
        try:
            logging.info("Deleting lock "+str(lock))
            self._lock_db(session)
            session.delete(lock)
            session.commit()
            self._unlock_db(session)
        finally:            
            session.close()
        return

    def _lock_db(self, session):
        """Utility to obtain a lock over the MySQL tables to ensure no race condition"""
        if(self.url.startswith('mysql')):
            session.execute('lock table resource_lock write')
            
    def _unlock_db(self, session):
        """Utility to obtain release a lock over the MySQL tables"""
        if(self.url.startswith('mysql')):
            session.execute('unlock tables')
            
    