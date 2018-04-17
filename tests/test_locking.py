# -*- coding: utf-8 -*-

import logging
import unittest
from ensembl_prodinf.resource_lock import ResourceLocker, LockException
from tempfile import mkstemp
import os

logging.basicConfig()

cname = 'testclient'
ruri = 'proto://myres/test'
rlock = 'read'
wlock = 'write'

class UtilsTest(unittest.TestCase):
    
    def get_db(self):
        (handle, dbfile) = mkstemp(suffix='.db')
        os.close(handle)
        return dbfile
        
    def run_test(self, test):
        dbfile = self.get_db()
        try:
            locker = ResourceLocker('sqlite:///'+str(dbfile))
            test(locker)
            return
        finally:
            os.remove(dbfile)
    
    def test_client(self):
        def ctest(locker):
            client = locker.get_client(cname)
            self.assertEqual(cname, client.name, "Client name correct")
            self.assertTrue(client.client_id>0, "Client has ID")
            client2 = locker.get_client(cname)
            self.assertEqual(client.client_id, client2.client_id, "Client retrieved")
            self.assertEqual(client.name, client2.name, "Client name retrieved")
            self.assertEqual(1, len(locker.get_clients()))
            locker.delete_client(cname)
            self.assertEqual(0, len(locker.get_clients()))
                        
        self.run_test(ctest)
        return

    def test_resource(self):
        def rtest(locker):
            res = locker.get_resource(ruri)
            self.assertEqual(ruri, res.uri, "Resource uri correct")
            self.assertTrue(res.resource_id>0, "Resource has ID")
            res2 = locker.get_resource(ruri)
            self.assertEqual(res.resource_id,res2.resource_id, "Resource retrieved")
            self.assertEqual(res.uri, res2.uri, "Resource uri retrieved")
            self.assertEqual(1, len(locker.get_resources()))
            locker.delete_resource(ruri)
            self.assertEqual(0, len(locker.get_resources()))
            
        self.run_test(rtest)
        return

    def test_read_lock(self):
        def rltest(locker):
            lock = locker.lock(cname, ruri, rlock)
            self.assertEqual(rlock, lock.lock_type, "Lock type correct")
            self.assertTrue(lock.resource_lock_id>0, "Lock has ID")       
            self.assertEqual(cname, lock.client.name, "Client correct")     
            self.assertEqual(ruri, lock.resource.uri, "Resource correct")  
            locks = [l for l in locker.get_locks() if(l.resource_lock_id == lock.resource_lock_id)]
            self.assertEqual(1, len(locks), "Lock exists")
            locker.unlock(lock)   
            locks = [l for l in locker.get_locks() if(l.resource_lock_id == lock.resource_lock_id)]
            self.assertEqual(0, len(locks), "Lock does not exist")            
            return
             
        self.run_test(rltest)
        return

    def test_write_lock(self):
        def wltest(locker):
            lock = locker.lock(cname, ruri, wlock)
            self.assertEqual(wlock, lock.lock_type, "Lock type correct")
            self.assertTrue(lock.resource_lock_id>0, "Lock has ID")       
            self.assertEqual(cname, lock.client.name, "Client correct")     
            self.assertEqual(ruri, lock.resource.uri, "Resource correct") 
            locks = [l for l in locker.get_locks() if(l.resource_lock_id == lock.resource_lock_id)]
            self.assertEqual(1, len(locks), "Lock exists")
            locker.unlock(lock)   
            locks = [l for l in locker.get_locks() if(l.resource_lock_id == lock.resource_lock_id)]
            self.assertEqual(0, len(locks), "Lock does not exist")       
            return
             
        self.run_test(wltest)
        return
    
    def test_readread_lock(self):
        def rltest(locker):
            lock1 = locker.lock(cname, ruri, rlock)
            self.assertEqual(rlock, lock1.lock_type, "Lock type correct")
            self.assertTrue(lock1.resource_lock_id>0, "Lock has ID")       
            self.assertEqual(cname, lock1.client.name, "Client correct")     
            self.assertEqual(ruri, lock1.resource.uri, "Resource correct")   
             
            lock2 = locker.lock(cname, ruri, rlock)
            self.assertEqual(rlock, lock2.lock_type, "Lock type correct")
            self.assertTrue(lock1.resource_lock_id>0, "Lock has ID")       
            self.assertEqual(cname, lock2.client.name, "Client correct")     
            self.assertEqual(ruri, lock2.resource.uri, "Resource correct")    
            return
             
        self.run_test(rltest)
        return

    def test_writeread_lock(self):
        def wrtest(locker):
            lock1 = locker.lock(cname, ruri, wlock)
            self.assertEqual(wlock, lock1.lock_type, "Lock type correct")
            self.assertTrue(lock1.resource_lock_id>0, "Lock has ID")       
            self.assertEqual(cname, lock1.client.name, "Client correct")     
            self.assertEqual(ruri, lock1.resource.uri, "Resource correct")               
            with self.assertRaises(LockException):
                locker.lock(cname, ruri, rlock)
            # unlock and retry
            locker.unlock(lock1)                
            locker.lock(cname, ruri, rlock)
            return
             
        self.run_test(wrtest)
        return
    
    def test_readwrite_lock(self):
        def rwtest(locker):
            lock1 = locker.lock(cname, ruri, rlock)
            self.assertEqual(rlock, lock1.lock_type, "Lock type correct")
            self.assertTrue(lock1.resource_lock_id>0, "Lock has ID")       
            self.assertEqual(cname, lock1.client.name, "Client correct")     
            self.assertEqual(ruri, lock1.resource.uri, "Resource correct")               
            with self.assertRaises(LockException):
                locker.lock(cname, ruri, wlock)  
            # unlock and retry
            locker.unlock(lock1)                
            locker.lock(cname, ruri, wlock)                              
            return
             
        self.run_test(rwtest)
        return
