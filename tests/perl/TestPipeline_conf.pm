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

            # additional tables needed for long multiplication pipeline's operation:
	    $self->db_cmd('CREATE TABLE result (job_id int(10), output TEXT, PRIMARY KEY (job_id))')
    ];
  }



1;
