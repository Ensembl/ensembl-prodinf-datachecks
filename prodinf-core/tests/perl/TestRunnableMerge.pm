package TestRunnableMerge;
use warnings;
use strict; 

use base qw/Bio::EnsEMBL::Production::Pipeline::Common::Base/;

use Carp qw(croak);

use Log::Log4perl qw/:easy/;
use Data::Dumper;

use JSON;

sub run {
  my $self = shift;
  my $token = $self->param_required('init_job_id');
  my $date = $self->param_required('date');
  my $names = $self->param_required('names');
  my $messages = $self->param_required('message');
  $self->dataflow_output_id(
	  {
	   job_id => $token,
	   output=>encode_json(
			       {
				messages=>$messages, 
				names=>$names, 
				date=>$date
			       }
			      )
	  },
	  2);
  return;
}

1;
