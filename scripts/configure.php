<?php
// CLI only. Password arrives through stdin and is never written in plain text.
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$dir=$argv[1] ?? ''; if ($dir==='') { fwrite(STDERR,"Usage: php configure.php /absolute/private/directory\n"); exit(1); }
if (!is_dir($dir) && !mkdir($dir,0700,true)) exit(1);
$path=$dir.'/config.php'; if (file_exists($path)) { fwrite(STDERR,"Existing owner configuration preserved.\n"); exit(0); }
$password=trim(stream_get_contents(STDIN)); if (strlen($password)<16) { fwrite(STDERR,"Use at least 16 characters.\n"); exit(1); }
$hash=password_hash($password,PASSWORD_DEFAULT);
file_put_contents($path,"<?php\nreturn ".var_export(['password_hash'=>$hash],true).";\n",LOCK_EX); chmod($path,0600);
echo "Owner configuration created.\n";
