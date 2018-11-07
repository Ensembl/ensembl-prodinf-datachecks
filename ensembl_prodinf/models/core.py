# -*- coding: utf-8 -*-
"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
Base = declarative_base()

__all__ = ['CoreInstance' ,'get_coredb_assembly']

class Meta(Base):
    __tablename__ = 'meta'

    meta_id = Column(Integer, primary_key=True)
    meta_key = Column(String)
    meta_value = Column(String)
    species_id = Column(Integer)

    def __repr__(self):
        return "<Meta(meta_id='%s',meta_key='%s', meta_value='%s', species_id='%s')>" % (
            self.meta_id, self.meta_key, self.meta_value, self.species_id)

Session = sessionmaker()

class CoreInstance:

    def __init__(self, url, timeout=3600):
        self.engine = create_engine(url, pool_recycle=timeout, echo=False)
        Session.configure(bind=self.engine)

    def get_core_species_assembly(self):
        """Retrieve a species assembly.default value from the core database meta table"""
        s = Session()
        try:
            MetaValues = s.query(Meta).filter(Meta.meta_key == 'assembly.default').first()
            return MetaValues
        finally:
                s.close()

def get_coredb_assembly(uri):
    inst = CoreInstance(uri)
    return inst.get_core_species_assembly()
