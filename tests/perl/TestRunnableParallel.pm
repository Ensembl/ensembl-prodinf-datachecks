package TestRunnableParallel;
use warnings;
use strict; 

use base qw/Bio::EnsEMBL::Production::Pipeline::Common::Base/;

use Carp qw(croak);

use Log::Log4perl qw/:easy/;
use Data::Dumper;

sub run {
  my $self = shift;
  my $name = $self->param_required('name');
  my $date = $self->param_required('date');
  croak if $name eq 'Bob';
  $self->dataflow_output_id(
	  {
	   message=>sprintf('Hello %s its %s', $name, $date)
	  },
	  2);
  return;
}

1;
