package TestPipeline_conf;
use warnings;
use strict;
use parent 'Bio::EnsEMBL::Hive::PipeConfig::EnsemblGeneric_conf';
use Bio::EnsEMBL::ApiVersion qw/software_version/;

sub pipeline_analyses {
  my $self = shift;
  return [
	  {
	   -logic_name => 'TestFactory',
	   -module =>
	   'TestFactory',
	   -meadow_type=> 'LOCAL',
	   -input_ids => [ ],    # required for automatic seeding
	   -parameters => {},
	   -flow_into => { '2->A' => ['TestRunnableParallel'],
			   'A->1' => ['TestRunnableMerge'] }
	  }, 
	  {
	   -logic_name => 'TestRunnableParallel',
	   -module =>
	   'TestRunnableParallel',
	   -meadow_type=> 'LOCAL',
	   -parameters    => {},
	   -hive_capacity => 8,
	   -flow_into     => ['TestRunnableDecorate']
	  },
	  {
	   -logic_name => 'TestRunnableDecorate',
	   -module =>
	   'TestRunnableParallel',
	   -meadow_type=> 'LOCAL',
	   -parameters    => {},
	   -hive_capacity => 8,
	   -flow_into     => {
			      2 => [ '?accu_name=message&accu_address=[]']			      
			     }
	  },
	  {
	   -logic_name => 'TestRunnableMerge',
	   -module =>
	   'TestRunnableMerge',
	   -meadow_type=> 'LOCAL',
	   -parameters    => {},
	   -hive_capacity => 8,
	   -flow_into     => {
			      2 => [ '?table_name=result']
			      
			     }
	  },
	  {
	   -logic_name => 'TestRunnable',
	   -module =>
	   'TestRunnable',
	   -meadow_type=> 'LOCAL',
	   -parameters    => {},
	   -hive_capacity => 8,
	   -flow_into     => {
			      2 => [ '?table_name=result']			      
			     }
	  }
	 ];
}

sub pipeline_create_commands {
    my ($self) = @_;
    return [
	    @{$self->SUPER::pipeline_create_commands},  # inheriting database and hive tables' creation
	    $self->db_cmd('CREATE TABLE result (job_id int(10), output TEXT, PRIMARY KEY (job_id))')
        $self->db_cmd('CREATE TABLE job_progress (job_progress_id int(11) NOT NULL AUTO_INCREMENT, job_id int(11) NOT NULL , message TEXT,  PRIMARY KEY (job_progress_id))'),
        $self->db_cmd('ALTER TABLE job_progress ADD INDEX (job_id)'),
        $self->db_cmd('ALTER TABLE job DROP KEY input_id_stacks_analysis'),
        $self->db_cmd('ALTER TABLE job MODIFY input_id TEXT')
    ];
  }



1;
