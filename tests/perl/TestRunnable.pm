package TestRunnable;
use warnings;
use strict; 

use base qw/Bio::EnsEMBL::Production::Pipeline::Common::Base/;

use Carp qw(croak);

use Log::Log4perl qw/:easy/;
use Data::Dumper;
use JSON;;

sub run {
  my $self = shift;
  my $token = $self->input_job()->dbID();
  my $name = $self->param_required('name');
  my $date = $self->param_required('date');
  croak if $name eq 'Bob';
  my $str = encode_json({message=>sprintf('Hello %s its %s but its a secret', $name, $date), name=>$name, date=>$date});
  print "$token $str\n";
  $self->dataflow_output_id(
			    {
			     job_id => $token,
			     output=>$str
			    },
			    2);
  return;
}

1;
