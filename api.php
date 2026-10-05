<?php
// api.php - Thin pass-through to tournament_bracket.py
$action = $_GET['action'] ?? 'init';

if ($action === 'export') {
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="tournament_participants.csv"');
    echo shell_exec('python3 tournament_bracket.py export');
    exit;
}

header('Content-Type: application/json; charset=utf-8');

if ($action === 'import') {
    $desc = [0 => ['pipe', 'r'], 1 => ['pipe', 'w']];
    $proc = proc_open('python3 tournament_bracket.py import', $desc, $pipes);
    fwrite($pipes[0], file_get_contents('php://input'));
    fclose($pipes[0]);
    echo stream_get_contents($pipes[1]);
    fclose($pipes[1]);
    proc_close($proc);
} elseif ($action === 'win') {
    $r = intval($_GET['r'] ?? 0);
    $m = intval($_GET['m'] ?? 0);
    $id = intval($_GET['id'] ?? 0);
    echo shell_exec("python3 tournament_bracket.py win $r $m $id");
} else {
    echo shell_exec('python3 tournament_bracket.py init');
}
