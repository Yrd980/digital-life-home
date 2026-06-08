const root = new URL('../', import.meta.url);
const port = Number(process.env.PORT || 8787);
const types = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp'
};

function safePath(pathname) {
  const clean = decodeURIComponent(pathname).replace(/^\/+/, '') || 'index.html';
  const url = new URL(clean, root);
  return url.href.startsWith(root.href) ? url : null;
}

Bun.serve({
  port,
  async fetch(request) {
    const url = new URL(request.url);
    const fileUrl = safePath(url.pathname);
    if (!fileUrl) return new Response('not found\n', {status: 404});
    const file = Bun.file(fileUrl);
    if (!(await file.exists())) return new Response('not found\n', {status: 404});
    const ext = fileUrl.pathname.match(/\.[^.]+$/)?.[0]?.toLowerCase() || '';
    return new Response(file, {headers: {'Content-Type': types[ext] || 'application/octet-stream'}});
  }
});

console.log(`Miri Deck UI: http://127.0.0.1:${port}`);
