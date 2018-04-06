from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
import datetime
import logging
logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
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

    def __init__(self, url, timeout=3600):
        engine = create_engine(url, pool_recycle=timeout, echo=False)
        Base.metadata.create_all(engine)
        Session.configure(bind=engine)

    def get_client(self, name):
        """Get or create a client with the given name"""
        return self._get_object(Client, name=name)
    
    def get_resource(self, uri):
        """Get or create a resource with the given URI"""
        return self._get_object(Resource, uri=uri)

    def _get_object(self, obj_type, **kwargs):
        """Fetch or create a basic object from the database.
        If the object is not present, create it.
        If it has already been created, return it.
        If a duplicate exists, retry the method.
        """
        session = Session()
        try:                    
            obj = session.query(obj_type).filter_by(**kwargs).first()
            if obj:
                return obj
            else:
                obj = obj_type(**kwargs)
                session.add(obj)
                session.commit()
                return obj
        except IntegrityError:
            # duplicate entry, so try again to fetch with a fresh session
            session.close()
            return self._get_object(obj_type, **kwargs)
        finally:
            session.close()    

    def _load(self, lock):
        lock.resource
        lock.client

    def get_locks(self, **kwargs):
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
            for l in locks: self._load(l)
            return locks
        finally:
            session.close()
             
    def lock(self, client_name, resource_uri, lock_type):
        client = self.get_client(client_name)
        resource = self.get_resource(resource_uri)
        session = Session()
        try:
            session.execute('lock table resource_lock write')
            if(lock_type == 'read'):
                # can only create if no write locks found on resource
                n_locks = session.query(ResourceLock).filter_by(resource=resource, lock_type='write').count()
                if(n_locks>0):
                    raise LockException("Write lock found on {} - cannot lock for reading".format(str(n_locks), resource_uri))
                else:
                    session.add(ResourceLock(resource=resource, client=client, lock_type=lock_type))
                    session.commit()                    
            elif(lock_type == 'write'):
                # can only create if no other locks found on resource
                n_locks = session.query(ResourceLock).filter_by(resource=resource).count()
                if(n_locks>0):
                    raise LockException("{} lock(s) found on {}".format(str(n_locks), resource_uri))
                else:
                    session.add(ResourceLock(resource=resource, client=client, lock_type=lock_type))
                    session.commit()                    
            else:
                raise ValueError("Unsupported lock_type".format(str(lock_type)))
            session.execute('unlock tables')
        finally:            
            session.close()
        return
            
    