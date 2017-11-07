package TestRunnableDecorate;
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
	   name=>$name,
	   date=>$date,
	   message=>$self->param_required('message')." lovely"
	  },
	  2);
  return;
}

1;
