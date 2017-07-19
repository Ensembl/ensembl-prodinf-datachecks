from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from .utils import dict_to_perl_string

import time
import json

Base = declarative_base()

class Analysis(Base):
    __tablename__ = 'analysis_base'

    analysis_id = Column(Integer, primary_key=True)
    logic_name = Column(String)
    
    def __repr__(self):
        return "<Analysis(analysis_id='%s', logic_name='%s')>" % (
            self.analysis_id, self.logic_name)

class Result(Base):
    __tablename__ = 'result'

    job_id = Column(Integer, primary_key=True)
    output = Column(String)

    def output_dict(self):
        return json.loads(self.output)

    def __repr__(self):
        return "<Result(job_id='%s', output='%s')>" % (
            self.job_id, self.output)

class LogMessage(Base):
    __tablename__ = 'log_message'

    log_message_id = Column(Integer, primary_key=True)
    job_id = Column(Integer)
    msg = Column(String)
    status = Column(String)
    is_error = Column(Integer)
    when_logged = Column(String)

    def __repr__(self):
        return "<LogMessage(log_message_id='%s', msg='%s')>" % (
            self.log_message_id, self.msg)


class Job(Base):
    __tablename__ = 'job'

    job_id = Column(Integer(), ForeignKey("result.job_id"), ForeignKey("log_message.job_id"), primary_key=True, autoincrement=True)
    input_id = Column(String)
    status = Column(String)
    prev_job_id = Column(Integer)
    semaphored_job_id = Column(Integer)
    semaphore_count = Column(Integer, default=0)
    
    analysis_id = Column(Integer, ForeignKey("analysis_base.analysis_id"))
    analysis = relationship("Analysis", uselist=False)

    result = relationship("Result", uselist=False)

    log_messages = relationship("LogMessage", viewonly=True)

    def __repr__(self):
        return "<Job(job_id='%s', analysis='%s', input_id='%s', status='%s', result='%s')>" % (
            self.job_id, self.analysis.logic_name, self.input_id, self.status, self.result.output if self.result != None else None)

Session = sessionmaker()

class HiveInstance:

    analysis_dict = dict()

    def __init__(self, url):
        engine = create_engine(url)
        Session.configure(bind=engine)

    def get_job_by_id(self, id):
        session = Session()
        return session.query(Job).filter(Job.job_id == id).first()

    def get_analysis_by_name(self, name):
        session = Session()
        return session.query(Analysis).filter(Analysis.logic_name==name).first()

    def create_job(self, analysis_name, input_data):
        input_data['timestamp'] = time.time()
        analysis = self.get_analysis_by_name(analysis_name)
        if analysis == None:
            raise ValueError("Analysis %s not found" % analysis_name)
        session = Session()
        try:
            job = Job(input_id=dict_to_perl_string(input_data), status='READY', analysis_id=analysis.analysis_id);
            session.add(job)
            session.commit()
            return job
        except:
            session.rollback()
            raise        

    def get_result_for_job_id(self, id):
        job = self.get_job_by_id(id)
        if job == None:
            raise ValueError("Job %s not found" % id)
        result = {"id":job.job_id}
        if job.status == 'DONE' and job.result!=None:
            result['status'] = 'complete'
            result['output'] = job.result.output_dict()
        else:
            result['status'] = self.get_job_tree_status(job)
        return result

    def get_job_tree_status(self, job):
        # check for semaphores
        if job.semaphore_count>0:
            return self.check_semaphores_for_job(job)
        else:
            if job.status == 'FAILED':
                return 'failed'
            elif job.status != 'DONE':
                return 'incomplete'
            else:
                session = Session()
                for child_job in session.query(Job).filter(Job.prev_job_id == job.job_id).all():
                    child_status = self.get_job_tree_status(child_job)
                    if child_status != 'complete':
                        return child_status
                return 'complete'

    def get_semaphored_jobs(self,job,status=None):
        session = Session()
        if status == None:
            return session.query(Job).filter(Job.semaphored_job_id==job.job_id).all()
        else:
            return session.query(Job).filter(Job.semaphored_job_id==job.job_id, Job.status == status).all()

    def check_semaphores_for_job(self, job):
        session = Session()
        status = 'complete'
        jobs  = dict(session.query(Job.status, func.count(Job.status)).filter(Job.semaphored_job_id==job.job_id).group_by(Job.status).all())
        if 'FAILED' in jobs and jobs['FAILED']>0:
            status = 'failed'
        elif ('READY' in jobs and jobs['READY']>0) or ('RUN' in jobs and jobs['RUN']>0): 
            status = 'incomplete'
        return status



