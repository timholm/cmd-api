const http = require('http');
const { exec } = require('child_process');

const PORT = process.env.PORT || 3000;
const CLAUDE_PATH = '/Users/tim/.local/bin/claude';

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  if (req.method === 'GET' && req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Command API running.\nPOST /run - shell commands\nPOST /claude - Claude Code prompts');
    return;
  }

  if (req.method === 'POST' && req.url === '/run') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { cmd } = JSON.parse(body);
        exec(cmd, { timeout: 30000 }, (error, stdout, stderr) => {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ stdout: stdout || '', stderr: stderr || '', code: error ? error.code || 1 : 0 }));
        });
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
      }
    });
    return;
  }

  if (req.method === 'POST' && req.url === '/claude') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { prompt } = JSON.parse(body);
        if (!prompt) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Missing prompt' }));
          return;
        }
        const logPrompt = prompt.length > 100 ? prompt.substring(0, 100) + '...' : prompt;
        console.log('[Claude] Received: ' + logPrompt);

        // Escape the prompt for shell - replace single quotes
        const escapedPrompt = prompt.replace(/'/g, "'\\''");
        const cmd = CLAUDE_PATH + " -p '" + escapedPrompt + "'";

        exec(cmd, { timeout: 300000, maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
          console.log('[Claude] Done with code ' + (error ? error.code || 1 : 0));
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({
            response: stdout || '',
            stderr: stderr || '',
            code: error ? error.code || 1 : 0
          }));
        });
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
      }
    });
    return;
  }

  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found' }));
});

server.listen(PORT, () => {
  console.log('Command API on port ' + PORT);
});
