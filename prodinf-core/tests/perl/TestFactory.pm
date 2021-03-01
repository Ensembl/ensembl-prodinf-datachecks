package TestFactory;
use warnings;
use strict; 

use base qw/Bio::EnsEMBL::Production::Pipeline::Common::Base/;

use Carp qw(croak);

use Log::Log4perl qw/:easy/;
use Data::Dumper;

sub run {
  my $self = shift;
  my $names = $self->param_required('names');
  my $date = localtime;
  # fan into 2
  for my $name (@{$names}) { 
    $self->dataflow_output_id(
			      {
			       name=>$name,
			       date=>$date
			      },
			      2);
  }
  # main semaphore flow to 1 with original input
  $self->dataflow_output_id(
			    {
			     init_job_id=>$self->input_job()->dbID(),
			     names=>$names,
			     date=>$date
			    },
			    1
			   );
  return;
}

1;
