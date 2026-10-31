<?php
declare(strict_types=1);
ini_set('display_errors', '0');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: no-referrer');
header('Content-Type: application/json; charset=utf-8');
function reply(array $data, int $code = 200): never { http_response_code($code); echo json_encode($data, JSON_THROW_ON_ERROR); exit; }
function fail(string $message, int $code = 400): never { reply(['error' => $message], $code); }
set_exception_handler(function (Throwable $e): never { error_log('MAK Design: '.$e->getMessage()); fail('The request could not be completed. Please try again.', 500); });
$private = getenv('MAK_PRIVATE_DIR') ?: dirname(__DIR__, 2).'/mak-design-private';
if (!is_file($private.'/config.php')) fail('Owner access has not been configured yet.', 503);
$config = require $private.'/config.php';
$db = new PDO('sqlite:'.$private.'/projects.sqlite', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$db->exec('PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON;');
$db->exec('CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, data BLOB NOT NULL, preview BLOB, version INTEGER NOT NULL DEFAULT 1, updated TEXT NOT NULL); CREATE TABLE IF NOT EXISTS links (hash TEXT PRIMARY KEY, project TEXT NOT NULL REFERENCES projects(id), expires INTEGER NOT NULL); CREATE TABLE IF NOT EXISTS attempts (ip TEXT PRIMARY KEY, failures INTEGER NOT NULL, started INTEGER NOT NULL);');
session_name('mak_design');
session_set_cookie_params(['lifetime' => 0, 'path' => '/', 'secure' => !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off', 'httponly' => true, 'samesite' => 'Strict']);
ini_set('session.use_strict_mode', '1');
session_start();
if (!isset($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(32));
if (isset($_SESSION['last']) && $_SESSION['last'] < time()-43200) { unset($_SESSION['owner']); }
$action = $_GET['action'] ?? 'session';
$method = $_SERVER['REQUEST_METHOD'];
function project(PDO $db, string $id): array { $q = $db->prepare('SELECT * FROM projects WHERE id=?'); $q->execute([$id]); $p = $q->fetch(PDO::FETCH_ASSOC); if (!$p) fail('Project not found.', 404); return $p; }
function bytes(mixed $value, int $max): string { if (!is_string($value) || strlen($value) > (int)ceil($max/3)*4+4) fail('File is too large.'); $b = base64_decode($value, true); if ($b === false || strlen($b) > $max) fail('Invalid file.'); return $b; }
// A client receives only the rendered preview, never the design archive or owner session.
if ($action === 'preview' && $method === 'GET') {
    $token = $_GET['token'] ?? '';
    if (!is_string($token) || !preg_match('/^[a-f0-9]{64}$/D', $token)) fail('This link is unavailable or expired.', 404);
    $q=$db->prepare('SELECT p.name,p.preview,p.updated FROM links l JOIN projects p ON p.id=l.project WHERE l.hash=? AND l.expires>?');
    $q->execute([hash('sha256', $token), time()]); $p=$q->fetch(PDO::FETCH_ASSOC);
    if (!$p || !$p['preview']) fail('This link is unavailable or expired.', 404);
    if (isset($_GET['image'])) { header('Content-Type: image/png'); header('Content-Disposition: inline; filename="design.png"'); echo $p['preview']; exit; }
    reply(['name'=>$p['name'], 'updated'=>$p['updated']]);
}
if ($action === 'session' && $method === 'GET') reply(['owner'=>!empty($_SESSION['owner']), 'csrf'=>$_SESSION['csrf']]);
$body=[];
if ($method === 'POST') {
    if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 45000000) fail('Request is too large.', 413);
    $raw=file_get_contents('php://input', false, null, 0, 45000001);
    if ($raw === false || strlen($raw)>45000000) fail('Request is too large.', 413);
    $body=json_decode($raw, true); if (!is_array($body)) fail('Invalid request.');
    if (!hash_equals($_SESSION['csrf'], $_SERVER['HTTP_X_CSRF_TOKEN'] ?? '')) fail('Please reload the page and try again.', 403);
}
if ($action === 'login' && $method === 'POST') {
    $ip=hash('sha256', $_SERVER['REMOTE_ADDR'] ?? 'unknown');
    $q=$db->prepare('SELECT * FROM attempts WHERE ip=?'); $q->execute([$ip]); $a=$q->fetch(PDO::FETCH_ASSOC);
    if ($a && (int)$a['started'] > time()-900 && (int)$a['failures'] >= 8) fail('Too many attempts. Please wait 15 minutes.', 429);
    $password=$body['password'] ?? '';
    if (!is_string($password) || strlen($password)>1024 || !password_verify($password, $config['password_hash'])) {
        $q=$db->prepare('INSERT INTO attempts(ip,failures,started) VALUES(?,1,?) ON CONFLICT(ip) DO UPDATE SET failures=CASE WHEN started<? THEN 1 ELSE failures+1 END, started=CASE WHEN started<? THEN excluded.started ELSE started END');
        $q->execute([$ip,time(),time()-900,time()-900]); fail('Incorrect password.', 401);
    }
    $db->prepare('DELETE FROM attempts WHERE ip=? OR started<?')->execute([$ip,time()-86400]);
    session_regenerate_id(true); $_SESSION['owner']=true; $_SESSION['last']=time(); $_SESSION['csrf']=bin2hex(random_bytes(32)); reply(['ok'=>true,'csrf'=>$_SESSION['csrf']]);
}
if (empty($_SESSION['owner'])) fail('Please sign in.', 401);
$_SESSION['last']=time();
if ($action==='logout' && $method==='POST') { $_SESSION=[]; session_destroy(); reply(['ok'=>true]); }
if ($action==='list' && $method==='GET') reply(['projects'=>$db->query('SELECT id,name,version,updated, preview IS NOT NULL AS hasPreview, (SELECT COUNT(*) FROM links WHERE project=projects.id AND expires>'.time().') AS links FROM projects ORDER BY updated DESC')->fetchAll(PDO::FETCH_ASSOC)]);
if ($action==='thumbnail' && $method==='GET') { $p=project($db,(string)($_GET['id'] ?? '')); if (!$p['preview']) fail('No preview saved.',404); header('Content-Type: image/png'); echo $p['preview']; exit; }
if ($action==='load' && $method==='GET') { $p=project($db,(string)($_GET['id'] ?? '')); reply(['id'=>$p['id'],'name'=>$p['name'],'data'=>base64_encode($p['data']),'version'=>(int)$p['version']]); }
if ($action==='save' && $method==='POST') {
    $id=$body['id'] ?? ''; if (!is_string($id) || ($id!=='' && !preg_match('/^[a-f0-9]{32}$/D',$id))) fail('Invalid project.');
    $name=$body['name'] ?? ''; if (!is_string($name) || trim($name)==='' || strlen($name)>160) fail('Use a project name under 160 characters.');
    $data=bytes($body['data'] ?? '', 24000000); if (!str_starts_with($data, "PK\x03\x04")) fail('Expected a FigCraft archive.');
    $preview=null;
    if (!empty($body['preview'])) { $preview=bytes($body['preview'], 8000000); $image=@getimagesizefromstring($preview); if (!$image || $image[2]!==IMAGETYPE_PNG || $image[0]*$image[1]>24000000) fail('Invalid PNG preview.'); }
    $db->beginTransaction();
    if ($id!=='') {
        project($db,$id);
        $q=$db->prepare('UPDATE projects SET name=?, data=?, preview=?,version=version+1,updated=? WHERE id=? AND version=?');
        $q->execute([trim($name),$data,$preview,gmdate('c'),$id,(int)($body['version'] ?? 0)]);
        if ($q->rowCount()!==1) { $db->rollBack(); fail('A newer save exists. Download your current design, then reopen the saved project.',409); }
    } else {
        $id=bin2hex(random_bytes(16)); $db->prepare('INSERT INTO projects(id,name,data,preview,updated) VALUES(?,?,?,?,?)')->execute([$id,trim($name),$data,$preview,gmdate('c')]);
    }
    $p=project($db,$id); $db->commit(); reply(['id'=>$id,'version'=>(int)$p['version'],'hasPreview'=>$p['preview']!==null]);
}
if ($action==='share' && $method==='POST') {
    $id=(string)($body['id'] ?? ''); $p=project($db,$id); if (!$p['preview']) fail('Save a preview before creating a client link.');
    $token=bin2hex(random_bytes(32)); $expires=time()+30*86400;
    $db->prepare('DELETE FROM links WHERE expires<?')->execute([time()]);
    $db->prepare('INSERT INTO links(hash,project,expires) VALUES(?,?,?)')->execute([hash('sha256',$token),$id,$expires]); reply(['token'=>$token,'expires'=>gmdate('c',$expires)]);
}
if ($action==='revoke' && $method==='POST') { $id=(string)($body['id'] ?? ''); project($db,$id); $db->prepare('DELETE FROM links WHERE project=?')->execute([$id]); reply(['ok'=>true]); }
fail('Unknown request.',404);
