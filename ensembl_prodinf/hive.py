from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from .utils import dict_to_perl_string, perl_string_to_python

import time
import json
import re

Base = declarative_base()

class Analysis(Base):

    __tablename__ = 'analysis_base'

    analysis_id = Column(Integer, primary_key=True)
    logic_name = Column(String)
    
    def __repr__(self):
        return "<Analysis(analysis_id='%s', logic_name='%s')>" % (
            self.analysis_id, self.logic_name)

class AnalysisData(Base):

    __tablename__ = 'analysis_data'

    analysis_data_id = Column(Integer, primary_key=True)
    data = Column(String)

    def __repr__(self):
        return "<AnalysisData(analysis_data_id='%s', data='%s')>" % (
            self.analysis_data_id, self.data)

class Result(Base):

    __tablename__ = 'result'

    job_id = Column(Integer, primary_key=True)
    output = Column(String)

    def output_dict(self):
        return json.loads(self.output)

    def __repr__(self):
        return "<Result(job_id='%s', output='%s')>" % (
            self.job_id, self.output)

class JobProgress(Base):

    __tablename__ = 'job_progress'

    job_progress_id = Column(Integer, primary_key=True)
    job_id = Column(Integer)
    message = Column(String)

    def __repr__(self):
        return "<JobProgress(job_progress_id='%s', job_id='%s', message='%s')>" % (
            self.job_progress_id, self.job_id, self.message)

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

class Role(Base):

    __tablename__ = 'role'

    role_id  = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey("worker.worker_id"))

    def __repr__(self):
        return "<Role(role_id='%s', worker_id='%s')>" % (
            self.role_id, self.worker_id)



class Worker(Base):

    __tablename__ = 'worker'

    worker_id = Column(Integer, primary_key=True)
    process_id = Column(String)

    def __repr__(self):
        return "<LogMessage(worker_id='%s', process_id='%s')>" % (
            self.worker_id, self.process_id)



class Job(Base):
    __tablename__ = 'job'

    job_id = Column(Integer(), ForeignKey("result.job_id"), ForeignKey("log_message.job_id"), primary_key=True, autoincrement=True)
    input_id = Column(String)
    status = Column(String)
    prev_job_id = Column(Integer)
    semaphored_job_id = Column(Integer)
    semaphore_count = Column(Integer, default=0)
    role_id = Column(Integer, ForeignKey("role.role_id"))
    
    analysis_id = Column(Integer, ForeignKey("analysis_base.analysis_id"))
    analysis = relationship("Analysis", uselist=False, lazy="joined")

    result = relationship("Result", uselist=False, lazy="joined")

    log_messages = relationship("LogMessage", viewonly=True)

    def __repr__(self):
        return "<Job(job_id='%s', analysis='%s', input_id='%s', status='%s', result='%s', role=%s)>" % (
            self.job_id, self.analysis.logic_name, self.input_id, self.status, self.result.output, self.role_id if self.result != None else None)

Session = sessionmaker()
class HiveInstance:

    analysis_dict = dict()

    def __init__(self, url, timeout=3600):
        engine = create_engine(url, pool_recycle=timeout, echo=False)
        Session.configure(bind=engine)

    def get_job_by_id(self, id):

        """ Retrieve a job given the unique surrogate ID """
        s = Session()
        try:
            job = s.query(Job).filter(Job.job_id == id).first()
            if(job == None):
                raise ValueError("Job %s not found" % id)
            job.result
            return job
        finally:
            s.close()

    def get_worker_id(self, id):

        """ Retrieve a worker_id for a given role_id """
        s = Session()
        try:
            return s.query(Role).filter(Role.role_id == id).first()
        finally:
            s.close()

    def get_jobs_failure_msg(self, id):

        """Get failures for all the parent and child jobs"""
        s = Session()
        try:
           failures = {}
           parent_job = self.get_job_by_id(id)
           if parent_job.status == 'FAILED':
            failures[id]=self.get_job_failure_msg_by_id(id).msg
           for child_job in s.query(Job).filter(Job.prev_job_id == id).all():
                if child_job.status == 'FAILED':
                    failures[child_job.job_id]=self.get_job_failure_msg_by_id(child_job.job_id).msg
           return failures
        finally:
            s.close()

    def get_job_failure_msg_by_id(self, id):

        """ Retrieve a job failure message or job child if exist"""
        s = Session()
        job = self.get_job_by_id(id)
        if job == None:
            raise ValueError("Job %s not found" % id)
        children_job = self.get_job_children(job)
        if children_job != None:
            try:
                return s.query(LogMessage).filter(LogMessage.job_id == children_job.job_id).order_by(LogMessage.log_message_id.desc()).first()
            finally:
                s.close()
        else:
            try:
                return s.query(LogMessage).filter(LogMessage.job_id == id).order_by(LogMessage.log_message_id.desc()).first()
            finally:
                s.close()

    def get_worker_process_id(self, id):

        """ Find a workers process_id """
        s = Session()
        try:
            return s.query(Worker).filter(Worker.worker_id==id).first()
        finally:
            s.close()

    def get_analysis_by_name(self, name):

        """ Find an analysis """
        s = Session()
        try:
            return s.query(Analysis).filter(Analysis.logic_name==name).first()
        finally:
            s.close()

    def create_job(self, analysis_name, input_data):

        """ Create a job for the supplied analysis and input hash 
        The input_data dict is converted to a Perl string before storing
        """

        input_data['timestamp'] = time.time()
        analysis = self.get_analysis_by_name(analysis_name)
        if analysis == None:
            raise ValueError("Analysis %s not found" % analysis_name)
        s = Session()
        try:
            job = Job(input_id=dict_to_perl_string(input_data), status='READY', analysis_id=analysis.analysis_id);
            s.add(job)
            s.commit()
            # force load of object
            job.analysis
            job.result
            return job
        except:
            s.rollback()
            raise        
        finally:
            s.close()

    def get_analysis_data_input(self, analysis_data_id):

        """ Get the job input stored in the analysis_data table. Get input from child job if exist"""
        s = Session()
        try:
            input_job = s.query(AnalysisData).filter(AnalysisData.analysis_data_id == analysis_data_id).first()
            return input_job
        finally:
            s.close()

    def get_result_for_job_id(self, id):

        job = self.get_job_by_id(id)
        if job == None:
            raise ValueError("Job %s not found" % id)
        children_job = self.get_job_children(job)
        if children_job != None:
            return self.get_result_for_job(children_job)
        else:
            return self.get_result_for_job(job)

    def get_result_for_job(self, job):
        """ Determine if the job has completed. If the job has semaphored children, they are also checked """
        """ Also return progress of jobs, completed and total """
        result = {"id":job.job_id}

        if re.search(r"^(_extended_data_id){1}(\s){1}(\d+){1}", job.input_id):
            extended_data = job.input_id.split(" ")
            job_input = self.get_analysis_data_input(extended_data[1])
            result['input'] = perl_string_to_python(job_input.data)
        else:
            result['input'] = perl_string_to_python(job.input_id)
        if job.status == 'DONE' and job.result!=None:
            result['status'] = 'complete'
            result['output'] = job.result.output_dict()
        else:
            result['status'] = self.get_job_tree_status(job)
            result['progress'] = self.get_jobs_progress(job)
        return result


    def get_jobs_progress(self, job):

        """ Check data in the job_progress table """
        """ alternatively, get jobs progress for parent and children jobs"""
        """ Return number of completed jobs and total of jobs"""
        """ If there is data in the job_progress table, return progress message"""
        s = Session()
        try:
            last_job_progress_msg=s.query(JobProgress).filter(JobProgress.job_id == job.job_id).order_by(JobProgress.job_progress_id.desc()).first()
            if last_job_progress_msg !=None:
                total=10
                complete=s.query(JobProgress).filter(JobProgress.job_id == job.job_id).count()
                return {"complete":complete,"total":total,"message":last_job_progress_msg.message}
            else:
               total=1
               complete = 0
               parent_job = self.get_job_by_id(job.job_id)
               if parent_job.status == 'DONE':
                complete +=1
               for child_job in s.query(Job).filter(Job.prev_job_id == job.job_id).all():
                    total +=1
                    if child_job.status == 'DONE':
                      complete +=1
               return {"complete":complete,"total":total}
        finally:
            s.close()

    def get_job_tree_status(self, job):

        """ Recursively check all children of a job """
        # check for semaphores
        if job.semaphore_count>0:
            return self.check_semaphores_for_job(job)
        else:
            if job.status == 'FAILED':
                return 'failed'
            elif job.status == 'READY':
                return 'submitted'
            elif job.status == 'RUN':
                return 'running'
            elif job.status == 'DONE':
                s = Session()
                try:
                    for child_job in s.query(Job).filter(Job.prev_job_id == job.job_id).all():
                        child_status = self.get_job_tree_status(child_job)
                        if child_status != 'complete':
                            return child_status
                    return 'complete'
                finally:
                    s.close()
            else:
                return 'incomplete'

    def get_job_children(self, job):

        """ Get children job id of a given parent job_id """
        s = Session()
        try:
            child_job = s.query(Job).filter(Job.prev_job_id == job.job_id).first()
            return child_job
        finally:
            s.close()

    def get_job_parent(self, job):

        """ Get parent job id of a given children job_id """
        s = Session()
        try:
            parent_job = s.query(Job).filter(Job.job_id == job.prev_job_id).first()
            return parent_job
        finally:
            s.close()

    def get_semaphored_jobs(self,job,status=None):

        """ Find all jobs that are semaphored children of the nominated job, optionall filtering by status 
        'complete' indicates that all children completed successfully
        'failed' indicates that at least one child has failed
        'incomplete' indicates that at least one child is running or ready
        """
        s = Session()
        try:
            if status == None:
                return s.query(Job).filter(Job.semaphored_job_id==job.job_id).all()
            else:
                return s.query(Job).filter(Job.semaphored_job_id==job.job_id, Job.status == status).all()
        finally:
            s.close()

    def check_semaphores_for_job(self, job):

        """ Find all jobs that are semaphored children of the nominated job, and check whether they have completed """

        s = Session()
        try:
            status = 'complete'
            jobs  = dict(s.query(Job.status, func.count(Job.status)).filter(Job.semaphored_job_id==job.job_id).group_by(Job.status).all())
            if 'FAILED' in jobs and jobs['FAILED']>0:
                status = 'failed'
            elif ('READY' in jobs and jobs['READY']>0) or ('RUN' in jobs and jobs['RUN']>0):
                status = 'incomplete'
            return status
        finally:
            s.close()

    def get_all_results(self, analysis_name):

        """Find all jobs from the specified analysis"""
        s = Session()
        try:
            jobs = s.query(Job).join(Analysis).filter(Analysis.logic_name == analysis_name).all()
            return list(map(lambda job: self.get_result_for_job(job), jobs))
        finally:
            s.close()

    def get_all_results_children(self, analysis_name):

        """Find all children jobs from the specified analysis
           Return parent job is children job doesn't exist"""
        s = Session()
        try:
            jobs = s.query(Job).join(Analysis).filter(Analysis.logic_name == analysis_name).all()
            return list(map(lambda job: self.get_result_for_job(self.get_job_children(job)) if (self.get_job_children(job) != None) else self.get_result_for_job(job), jobs))
        finally:
            s.close()
        
    def delete_job(self, job):
        children_job=self.get_job_children(job)
        parent_job=self.get_job_parent(job)
        if children_job != None:
            s = Session()
            try:
                print "Deleting children job "+str(children_job.job_id)
                if(children_job.result != None):
                    s.delete(children_job.result)
                s.delete(children_job)
                s.commit()
            except:
                s.rollback()
                raise
            finally:
                s.close()
        if parent_job != None:
            s = Session()
            try:
                print "Deleting parent job "+str(parent_job.job_id)
                if(parent_job.result != None):
                    s.delete(parent_job.result)
                s.delete(parent_job)
                s.commit()
            except:
                s.rollback()
                raise
            finally:
                s.close()
        try:
            s = Session()
            print "Deleting job "+str(job.job_id)
            if(job.result != None):
                s.delete(job.result)
            s.delete(job)
            s.commit()
        except:
            s.rollback()
            raise
        finally:
            s.close()
        
