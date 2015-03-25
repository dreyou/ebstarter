package handler;

use nginx;

my $html = <<'END_HTML';

<h1>Service was stopped!</h1>
<p>Please come back after 2-3 minutes, when service will be ready.</p>

END_HTML


sub handler {
    my $r = shift;
    my $app = $r->variable('app');
    my $src = $r->variable('src');

    $r->send_http_header("text/html");
    return OK if $r->header_only;

    $r->print($html);

    $r->flush();

    my $path = __FILE__;

    $path=~s/\/[\.\w\-_]+$//;

    my $err = "";

    my $cmd = "$path/sendm.sh create $app $src";

    exec($cmd) or $err = "couldn't $cmd foo: $!";

    return OK;
}

1;
__END__
