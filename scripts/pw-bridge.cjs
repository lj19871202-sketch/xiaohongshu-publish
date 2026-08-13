const http = require('http');
const fs = require('fs');
const path = require('path');

// 自动定位 playwright-core，查找顺序：
// 1) 环境变量 PW_PLAYWRIGHT_MODULES 指定的 node_modules 目录；
// 2) 仓库本地 node_modules（由 scripts/setup.ps1 安装）；
// 3) Codex 运行库目录（LOCALAPPDATA\OpenAI\Codex\runtimes\cua_node\<版本>\bin\node_modules）。
function findPlaywrightCoreModules() {
  const directCandidates = [];
  const scanRoots = [];
  if (process.env.PW_PLAYWRIGHT_MODULES) directCandidates.push(process.env.PW_PLAYWRIGHT_MODULES);
  directCandidates.push(path.join(__dirname, '..', 'node_modules'));
  if (process.env.LOCALAPPDATA) {
    scanRoots.push(path.join(process.env.LOCALAPPDATA, 'OpenAI', 'Codex', 'runtimes', 'cua_node'));
  }
  for (const dir of directCandidates) {
    if (fs.existsSync(path.join(dir, 'playwright-core'))) return dir;
  }
  for (const root of scanRoots) {
    let dirs = [];
    try { dirs = fs.readdirSync(root); } catch (e) { continue; }
    for (const dir of dirs) {
      const modules = path.join(root, dir, 'bin', 'node_modules');
      if (fs.existsSync(path.join(modules, 'playwright-core'))) return modules;
    }
  }
  throw new Error('未找到 playwright-core。请运行 scripts/setup.ps1 自动安装，或设置环境变量 PW_PLAYWRIGHT_MODULES 指向包含 playwright-core 的 node_modules 目录');
}

const { chromium } = require(path.join(findPlaywrightCoreModules(), 'playwright-core'));

const BRIDGE_DIR = __dirname;
const PORT_FILE = path.join(BRIDGE_DIR, 'pw.port');
const LOG_FILE = path.join(BRIDGE_DIR, 'pw.log');
const CDP = 'http://127.0.0.1:9222';

function log(...args) {
  const line = `[${new Date().toISOString()}] ${args.join(' ')}`;
  try { fs.appendFileSync(LOG_FILE, line + '\n'); } catch (e) {}
}

let browser = null;
let connecting = null;

async function getBrowser() {
  if (browser && browser.isConnected()) return browser;
  if (connecting) return connecting;
  connecting = (async () => {
    const b = await chromium.connectOverCDP(CDP, { timeout: 20000 });
    browser = b;
    log('BROWSER CONNECTED');
    b.on('disconnected', () => { log('BROWSER DISCONNECTED'); browser = null; });
    return b;
  })();
  try {
    return await connecting;
  } finally {
    connecting = null;
  }
}

async function exec(code, timeoutMs) {
  const b = await getBrowser();
  let pages;
  try { pages = b.contexts().flatMap(c => c.pages()); } catch (e) { pages = []; }
  const page = pages.find(p => !p.isClosed()) || null;
  const sandbox = { browser: b, pages, page };
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
  const fn = new AsyncFunction('browser', 'pages', 'page', 'fs', 'path', code);
  const timer = new Promise((_, rej) => setTimeout(() => rej(new Error('exec timed out')), timeoutMs || 120000));
  return await Promise.race([fn(browser, pages, page, fs, path), timer]);
}

const server = http.createServer(async (req, res) => {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  const body = [];
  req.on('data', c => body.push(c));
  req.on('end', async () => {
    let payload = {};
    try { payload = body.length ? JSON.parse(Buffer.concat(body).toString('utf8')) : {}; } catch (e) {}
    try {
      if (req.method === 'GET' && req.url === '/health') {
        res.end(JSON.stringify({ ok: true, connected: !!(browser && browser.isConnected()) }));
        return;
      }
      if (req.method === 'POST' && req.url === '/exec') {
        const result = await exec(String(payload.code || ''), payload.timeout_ms);
        res.end(JSON.stringify({ ok: true, result }));
        return;
      }
      res.statusCode = 404;
      res.end(JSON.stringify({ ok: false, error: 'not found' }));
    } catch (e) {
      res.statusCode = 500;
      res.end(JSON.stringify({ ok: false, error: String(e && e.message || e) }));
    }
  });
});

server.listen(0, '127.0.0.1', () => {
  const port = server.address().port;
  fs.writeFileSync(PORT_FILE, String(port), 'utf8');
  log('PW BRIDGE READY on port', port);
  console.log('PW_BRIDGE_READY ' + port);
});

process.on('SIGTERM', () => {
  try { if (browser) browser.close(); } catch (e) {}
  process.exit(0);
});
