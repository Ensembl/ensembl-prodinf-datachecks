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

__all__ = ['CoreInstance', 'get_division']

class Meta(Base):
    __tablename__ = 'meta'

    meta_id = Column(Integer, primary_key=True)
    meta_key = Column(String)
    meta_value = Column(String)

    def __repr__(self):
        return "<Meta(meta_id='%s',meta_key='%s', meta_value='%s')>" % (
            self.meta_id, self.meta_key, self.meta_value)


Session = sessionmaker()



class CoreInstance:

    __division = None

    def __init__(self, url, timeout=3600):
        self.engine = create_engine(url, pool_recycle=timeout, echo=False)
        Session.configure(bind=self.engine)

    def __get_meta_value(self, meta_key):
        s = Session()
        try:
            meta = s.query(Meta).filter(Meta.meta_key == meta_key).first()
            return meta.meta_value
        finally:
            s.close()

    @property
    def division(self):
        if self.__division is None:
            self.__division = self.__get_meta_value('species.division')
        return self.__division

def get_division(uri, db_type):
    if db_type == "variation" or db_type == "funcgen":
        uri = uri.replace("_variation_", "_core_").replace("_funcgen_","_core_")
    inst = CoreInstance(uri)
    division_meta = inst.division
    division = str(division_meta).replace('Ensembl','')
    return division.lower()
