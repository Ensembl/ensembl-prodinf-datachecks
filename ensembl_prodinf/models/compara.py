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

__all__ = ['ComparaInstance', 'check_grch37']

class GenomeDb(Base):
    __tablename__ = 'genome_db'

    genome_db_id = Column(Integer, primary_key=True)
    assembly = Column(String)
    name = Column(String)

    def __repr__(self):
        return "<GenomeDb(genome_db_id='%s',assembly='%s', name='%s')>" % (
            self.genome_db_id, self.assembly, self.name)

Session = sessionmaker()



class ComparaInstance:

    def __init__(self, url, timeout=3600):
        self.engine = create_engine(url, pool_recycle=timeout, echo=False)
        Session.configure(bind=self.engine)

    def get_compara_species_assembly(self,species):
        s = Session()
        try:
            genome_db = s.query(GenomeDb).filter(GenomeDb.name == species).first()
            return genome_db
        finally:
            s.close()

    def is_GRCh37(self, species):
        gen_db = self.get_compara_species_assembly(species)
        if gen_db:
            return gen_db.assembly == 'GRCh37'
        else:
            return 0

def check_grch37(uri, species):
    inst = ComparaInstance(uri)
    return inst.is_GRCh37(species)
