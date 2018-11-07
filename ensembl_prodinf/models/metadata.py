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
from sqlalchemy import Column, Date, Enum, ForeignKey, Index, LargeBinary, String, TIMESTAMP, Text, text, create_engine
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TINYINT, VARCHAR
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata

__all__ = ['MetadataInstance' ,'get_metadb_assembly', 'get_previous_assembly_db_list']


class LoadAble(object):
    _load_map = dict()
    
    def __repr__(self):
        class_name = self.__class__.__name__
        attributes = {name: getattr(self, name) for name in dir(self) if
                      isinstance(getattr(self, name), (type(None), str, int, float, bool))}
        return '<{}({})>'.format(class_name, attributes)

class Assembly(LoadAble,Base):
    __tablename__ = 'assembly'

    def __dir__(self):
        return ['assembly_id', 'assembly_accession', 'assembly_name', 'assembly_default', 'assembly_ucsc', 'assembly_level', 'base_count']

    assembly_id = Column(INTEGER(10), primary_key=True)
    assembly_accession = Column(String(16), unique=True)
    assembly_name = Column(String(200), nullable=False)
    assembly_default = Column(String(200), nullable=False)
    assembly_ucsc = Column(String(16))
    assembly_level = Column(String(50), nullable=False)
    base_count = Column(BIGINT(20), nullable=False)


class DataRelease(LoadAble,Base):
    __tablename__ = 'data_release'
    __table_args__ = (
        Index('ensembl_version', 'ensembl_version', 'ensembl_genomes_version', unique=True),
    )
    def __dir__(self):
        return ['data_release_id', 'ensembl_version', 'ensembl_genomes_version', 'release_date', 'is_current']

    data_release_id = Column(INTEGER(10), primary_key=True)
    ensembl_version = Column(INTEGER(10), nullable=False)
    ensembl_genomes_version = Column(INTEGER(10))
    release_date = Column(Date, nullable=False)
    is_current = Column(TINYINT(3), nullable=False, server_default=text("'0'"))


class Division(LoadAble,Base):
    __tablename__ = 'division'

    def __dir__(self):
        return ['division_id', 'name', 'short_name']

    division_id = Column(INTEGER(10), primary_key=True)
    name = Column(String(32), nullable=False, unique=True)
    short_name = Column(String(8), nullable=False, unique=True)


class Organism(LoadAble,Base):
    __tablename__ = 'organism'

    def __dir__(self):
        return ['organism_id', 'taxonomy_id', 'is_reference', 'species_taxonomy_id', 'name', 'url_name', 'display_name', 'scientific_name', 'strain', 'serotype', 'description', 'image']

    organism_id = Column(INTEGER(10), primary_key=True)
    taxonomy_id = Column(INTEGER(10), nullable=False)
    is_reference = Column(TINYINT(3), nullable=False, server_default=text("'0'"))
    species_taxonomy_id = Column(INTEGER(10), nullable=False)
    name = Column(String(128), nullable=False, unique=True)
    url_name = Column(String(128), nullable=False)
    display_name = Column(String(128), nullable=False)
    scientific_name = Column(String(128), nullable=False)
    strain = Column(String(128))
    serotype = Column(String(128))
    description = Column(Text)
    image = Column(LargeBinary)


class AssemblySequence(LoadAble,Base):
    __tablename__ = 'assembly_sequence'
    __table_args__ = (
        Index('name_acc', 'assembly_id', 'name', 'acc', unique=True),
    )

    def __dir__(self):
        return ['assembly_sequence_id', 'assembly_id', 'name', 'acc']

    assembly_sequence_id = Column(INTEGER(10), primary_key=True)
    assembly_id = Column(ForeignKey(u'assembly.assembly_id', ondelete=u'CASCADE'), nullable=False)
    name = Column(String(40), nullable=False, index=True)
    acc = Column(String(24), index=True)

    assembly = relationship(u'Assembly')


class ComparaAnalysi(LoadAble,Base):
    __tablename__ = 'compara_analysis'
    __table_args__ = (
        Index('division_method_set_name_dbname', 'division_id', 'method', 'set_name', 'dbname', unique=True),
    )

    def __dir__(self):
        return ['compara_analysis_id', 'data_release_id', 'division_id', 'method', 'set_name', 'dbname']

    compara_analysis_id = Column(INTEGER(10), primary_key=True)
    data_release_id = Column(INTEGER(10), nullable=False)
    division_id = Column(ForeignKey(u'division.division_id'), nullable=False)
    method = Column(String(50), nullable=False)
    set_name = Column(String(128))
    dbname = Column(String(64), nullable=False)

    division = relationship(u'Division')


class DataReleaseDatabase(LoadAble,Base):
    __tablename__ = 'data_release_database'
    __table_args__ = (
        Index('id_dbname', 'data_release_id', 'dbname', unique=True),
    )

    def __dir__(self):
        return ['data_release_database_id', 'data_release_id', 'dbname', 'type', 'division_id']

    data_release_database_id = Column(INTEGER(10), primary_key=True)
    data_release_id = Column(ForeignKey(u'data_release.data_release_id'), nullable=False)
    dbname = Column(String(64), nullable=False)
    type = Column(Enum(u'mart', u'ontology', u'ids', u'other'), server_default=text("'other'"))
    division_id = Column(ForeignKey(u'division.division_id'), nullable=False, index=True)

    data_release = relationship(u'DataRelease')
    division = relationship(u'Division')


class Genome(LoadAble,Base):
    __tablename__ = 'genome'
    __table_args__ = (
        Index('release_genome', 'data_release_id', 'genome_id', unique=True),
    )

    def __dir__(self):
        return ['genome_id', 'data_release_id', 'assembly_id', 'organism_id', 'genebuild', 'division_id', 'has_pan_compara', 'has_variations', 'has_peptide_compara', 'has_genome_alignments', 'has_synteny', 'has_other_alignments']

    genome_id = Column(INTEGER(10), primary_key=True)
    data_release_id = Column(ForeignKey(u'data_release.data_release_id'), nullable=False)
    assembly_id = Column(ForeignKey(u'assembly.assembly_id'), nullable=False, index=True)
    organism_id = Column(ForeignKey(u'organism.organism_id'), nullable=False, index=True)
    genebuild = Column(String(64), nullable=False)
    division_id = Column(ForeignKey(u'division.division_id'), nullable=False, index=True)
    has_pan_compara = Column(TINYINT(3), nullable=False, server_default=text("'0'"))
    has_variations = Column(TINYINT(3), nullable=False, server_default=text("'0'"))
    has_peptide_compara = Column(TINYINT(3), nullable=False, server_default=text("'0'"))
    has_genome_alignments = Column(TINYINT(3), nullable=False, server_default=text("'0'"))
    has_synteny = Column(TINYINT(3), nullable=False, server_default=text("'0'"))
    has_other_alignments = Column(TINYINT(3), nullable=False, server_default=text("'0'"))

    assembly = relationship(u'Assembly')
    data_release = relationship(u'DataRelease')
    division = relationship(u'Division')
    organism = relationship(u'Organism')


class OrganismAlia(LoadAble,Base):
    __tablename__ = 'organism_alias'
    __table_args__ = (
        Index('id_alias', 'organism_id', 'alias', unique=True),
    )

    def __dir__(self):
        return ['organism_alias_id', 'organism_id', 'alias']

    organism_alias_id = Column(INTEGER(10), primary_key=True)
    organism_id = Column(ForeignKey(u'organism.organism_id', ondelete=u'CASCADE'), nullable=False)
    alias = Column(VARCHAR(255))

    organism = relationship(u'Organism')


class OrganismPublication(LoadAble,Base):
    __tablename__ = 'organism_publication'
    __table_args__ = (
        Index('id_publication', 'organism_id', 'publication', unique=True),
    )

    def __dir__(self):
        return ['organism_publication_id', 'organism_id', 'publication']

    organism_publication_id = Column(INTEGER(10), primary_key=True)
    organism_id = Column(ForeignKey(u'organism.organism_id', ondelete=u'CASCADE'), nullable=False)
    publication = Column(String(64))

    organism = relationship(u'Organism')


class ComparaAnalysisEvent(LoadAble,Base):
    __tablename__ = 'compara_analysis_event'

    def __dir__(self):
        return ['compara_analysis_event_id', 'compara_analysis_id', 'type', 'source', 'creation_time', 'details']

    compara_analysis_event_id = Column(INTEGER(10), primary_key=True)
    compara_analysis_id = Column(ForeignKey(u'compara_analysis.compara_analysis_id', ondelete=u'CASCADE'), nullable=False, index=True)
    type = Column(String(32), nullable=False)
    source = Column(String(128))
    creation_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    details = Column(Text)

    compara_analysis = relationship('ComparaAnalysi')


class DataReleaseDatabaseEvent(LoadAble,Base):
    __tablename__ = 'data_release_database_event'

    def __dir__(self):
        return ['data_release_database_event_id', 'data_release_database_id', 'type', 'source', 'creation_time', 'details']

    data_release_database_event_id = Column(INTEGER(10), primary_key=True)
    data_release_database_id = Column(ForeignKey(u'data_release_database.data_release_database_id', ondelete=u'CASCADE'), nullable=False, index=True)
    type = Column(String(32), nullable=False)
    source = Column(String(128))
    creation_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    details = Column(Text)

    data_release_database = relationship(u'DataReleaseDatabase')


class GenomeComparaAnalysi(LoadAble,Base):
    __tablename__ = 'genome_compara_analysis'
    __table_args__ = (
        Index('genome_compara_analysis_key', 'genome_id', 'compara_analysis_id', unique=True),
    )

    def __dir__(self):
        return ['genome_compara_analysis_id', 'genome_id', 'compara_analysis_id']

    genome_compara_analysis_id = Column(INTEGER(10), primary_key=True)
    genome_id = Column(ForeignKey(u'genome.genome_id', ondelete=u'CASCADE'), nullable=False)
    compara_analysis_id = Column(ForeignKey(u'compara_analysis.compara_analysis_id', ondelete=u'CASCADE'), nullable=False, index=True)

    compara_analysis = relationship('ComparaAnalysi')
    genome = relationship(u'Genome')


class GenomeDatabase(LoadAble,Base):
    __tablename__ = 'genome_database'
    __table_args__ = (
        Index('id_dbname', 'genome_id', 'dbname', unique=True),
        Index('dbname_species_id', 'dbname', 'species_id', unique=True)
    )

    def __dir__(self):
        return ['genome_database_id', 'genome_id', 'dbname', 'species_id']

    genome_database_id = Column(INTEGER(10), primary_key=True)
    genome_id = Column(ForeignKey(u'genome.genome_id', ondelete=u'CASCADE'), nullable=False)
    dbname = Column(String(64), nullable=False)
    species_id = Column(INTEGER(10), nullable=False)
    type = Column(Enum(u'core', u'funcgen', u'variation', u'otherfeatures', u'rnaseq', u'cdna'))

    genome = relationship(u'Genome')


class GenomeEvent(LoadAble,Base):
    __tablename__ = 'genome_event'

    def __dir__(self):
        return ['genome_event_id', 'genome_id', 'type', 'source', 'creation_time', 'details']

    genome_event_id = Column(INTEGER(10), primary_key=True)
    genome_id = Column(ForeignKey(u'genome.genome_id', ondelete=u'CASCADE'), nullable=False, index=True)
    type = Column(String(32), nullable=False)
    source = Column(String(128))
    creation_time = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    details = Column(Text)

    genome = relationship(u'Genome')


class GenomeAlignment(LoadAble,Base):
    __tablename__ = 'genome_alignment'
    __table_args__ = (
        Index('id_type_key', 'genome_id', 'type', 'name', 'genome_database_id', unique=True),
    )

    def __dir__(self):
        return ['genome_alignment_id', 'genome_id', 'type', 'name', 'count', 'genome_database_id']

    genome_alignment_id = Column(INTEGER(10), primary_key=True)
    genome_id = Column(ForeignKey(u'genome.genome_id', ondelete=u'CASCADE'), nullable=False)
    type = Column(String(32), nullable=False)
    name = Column(String(128), nullable=False)
    count = Column(INTEGER(10), nullable=False)
    genome_database_id = Column(ForeignKey(u'genome_database.genome_database_id', ondelete=u'CASCADE'), nullable=False, index=True)

    genome_database = relationship(u'GenomeDatabase')
    genome = relationship(u'Genome')


class GenomeAnnotation(LoadAble,Base):
    __tablename__ = 'genome_annotation'
    __table_args__ = (
        Index('id_type', 'genome_id', 'type', 'genome_database_id', unique=True),
    )

    def __dir__(self):
        return ['genome_annotation_id', 'genome_id', 'type', 'value', 'genome_database_id']

    genome_annotation_id = Column(INTEGER(10), primary_key=True)
    genome_id = Column(ForeignKey(u'genome.genome_id', ondelete=u'CASCADE'), nullable=False)
    type = Column(String(32), nullable=False)
    value = Column(String(128), nullable=False)
    genome_database_id = Column(ForeignKey(u'genome_database.genome_database_id', ondelete=u'CASCADE'), nullable=False, index=True)

    genome_database = relationship(u'GenomeDatabase')
    genome = relationship(u'Genome')


class GenomeFeature(LoadAble,Base):
    __tablename__ = 'genome_feature'
    __table_args__ = (
        Index('id_type_analysis', 'genome_id', 'type', 'analysis', 'genome_database_id', unique=True),
    )

    def __dir__(self):
        return ['genome_feature_id', 'genome_id', 'type', 'analysis', 'count', 'genome_database_id']

    genome_feature_id = Column(INTEGER(10), primary_key=True)
    genome_id = Column(ForeignKey(u'genome.genome_id', ondelete=u'CASCADE'), nullable=False)
    type = Column(String(32), nullable=False)
    analysis = Column(String(128), nullable=False)
    count = Column(INTEGER(10), nullable=False)
    genome_database_id = Column(ForeignKey(u'genome_database.genome_database_id', ondelete=u'CASCADE'), nullable=False, index=True)

    genome_database = relationship(u'GenomeDatabase')
    genome = relationship(u'Genome')


class GenomeVariation(LoadAble,Base):
    __tablename__ = 'genome_variation'
    __table_args__ = (
        Index('id_type_key', 'genome_id', 'type', 'name', 'genome_database_id', unique=True),
    )

    def __dir__(self):
        return ['genome_variation_id', 'genome_id', 'type', 'name', 'count', 'genome_database_id']

    genome_variation_id = Column(INTEGER(10), primary_key=True)
    genome_id = Column(ForeignKey(u'genome.genome_id', ondelete=u'CASCADE'), nullable=False)
    type = Column(String(32), nullable=False)
    name = Column(String(128), nullable=False)
    count = Column(INTEGER(10), nullable=False)
    genome_database_id = Column(ForeignKey(u'genome_database.genome_database_id', ondelete=u'CASCADE'), nullable=False, index=True)

    genome_database = relationship(u'GenomeDatabase')
    genome = relationship(u'Genome')

Session = sessionmaker()

class MetadataInstance:

    def __init__(self, url, timeout=3600):
        self.engine = create_engine(url, pool_recycle=timeout, echo=False)
        Session.configure(bind=self.engine)

    def get_genome_from_organism_release(self,species,release):
        """Retrieve the genome data for a given species and release"""
        s = Session()
        try:
            organism = s.query(Organism).filter(Organism.name == species).first()
            if organism:
                for data_release_id in s.query(DataRelease).filter(DataRelease.ensembl_version == release).all():
                    if data_release_id:
                        genome = s.query(Genome).filter(Genome.organism_id == organism.organism_id,Genome.data_release_id == data_release_id.data_release_id).first()
                        if genome:
                            return genome
        finally:
                s.close()
    
    def get_genome_assembly(self,species,release):
        """Retrieve the Assembly information from a genome for a given species and release"""
        s = Session()
        try:
            genome = self.get_genome_from_organism_release(species,release)
            if genome:
                assembly = s.query(Assembly).filter(Assembly.assembly_id == genome.assembly_id ).first()
                return assembly
        finally:
            s.close()
        
    def get_genome_database_list(self,species,release):
        """Retrieve databases associated with a genome for a given species and release"""
        s = Session()
        genome_database_list=[]
        try:
            genome = self.get_genome_from_organism_release(species,release)
            if genome:
                genome_databases = s.query(GenomeDatabase).filter(GenomeDatabase.genome_id == genome.genome_id ).all()
                for genome_database in genome_databases:
                     genome_database_list.append(genome_database.dbname)
                return genome_database_list
        finally:
            s.close()

def get_metadb_assembly(uri,species,release):
    inst = MetadataInstance(uri)
    return inst.get_genome_assembly(species,release)

def get_previous_assembly_db_list(uri,species,release):
    inst = MetadataInstance(uri)
    return inst.get_genome_database_list(species,release)
