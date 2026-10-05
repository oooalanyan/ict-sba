import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { execFileSync } from 'child_process';
import path from 'path';
import { defineConfig } from 'vite';

export default defineConfig(() => {
  return {
    plugins: [
      react(),
      tailwindcss(),
      {
        name: 'python-api-bridge',
        configureServer(server) {
          server.middlewares.use('/api.php', (req, res) => {
            const url = new URL(req.url || '', 'http://localhost');
            const action = url.searchParams.get('action') || 'init';

            if (action === 'export') {
              res.setHeader('Content-Type', 'text/csv; charset=utf-8');
              res.setHeader('Content-Disposition', 'attachment; filename="tournament_participants.csv"');
              const out = execFileSync('python3', ['tournament_bracket.py', 'export'], { encoding: 'utf-8' });
              res.end(out);
              return;
            }

            res.setHeader('Content-Type', 'application/json; charset=utf-8');

            if (action === 'import') {
              let body = '';
              req.on('data', chunk => { body += chunk; });
              req.on('end', () => {
                const out = execFileSync('python3', ['tournament_bracket.py', 'import'], {
                  input: body,
                  encoding: 'utf-8'
                });
                res.end(out);
              });
            } else if (action === 'win') {
              const r = url.searchParams.get('r') || '0';
              const m = url.searchParams.get('m') || '0';
              const id = url.searchParams.get('id') || '0';
              const out = execFileSync('python3', ['tournament_bracket.py', 'win', r, m, id], { encoding: 'utf-8' });
              res.end(out);
            } else {
              const out = execFileSync('python3', ['tournament_bracket.py', 'init'], { encoding: 'utf-8' });
              res.end(out);
            }
          });
        }
      }
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      hmr: process.env.DISABLE_HMR !== 'true',
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
    },
  };
});
