<?php
// Simple PHP script to load and save CSV (api.php)
header('Content-Type: application/json; charset=utf-8');
$file = 'participants_sample.csv';
$action = $_GET['action'] ?? 'load';

if ($action === 'load') {
    $players = [];
    if (($f = fopen($file, 'r')) !== false) {
        fgetcsv($f); // Skip header row
        while (($row = fgetcsv($f)) !== false) {
            if (count($row) >= 4) {
                $id = intval($row[0]);
                $players[$id] = [
                    'name' => trim($row[1]),
                    'school' => trim($row[2]),
                    'is_seed' => strtolower(trim($row[3])) === 'true'
                ];
            }
        }
        fclose($f);
    }
    echo json_encode(['players' => $players]);
} elseif ($action === 'save') {
    $data = json_decode(file_get_contents('php://input'), true);
    if (!empty($data['players']) && ($f = fopen($file, 'w')) !== false) {
        fputcsv($f, ['player_id', 'name', 'school', 'is_seed']);
        foreach ($data['players'] as $id => $p) {
            fputcsv($f, [$id, $p['name'], $p['school'], $p['is_seed'] ? 'True' : 'False']);
        }
        fclose($f);
        echo json_encode(['status' => 'ok']);
    }
}
