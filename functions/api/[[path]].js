// Keikenchi API — Cloudflare Pages Functions + D1 (binding: DB)
// Accounts (username+password), personal board (map + achievements + notes + dates),
// plus anonymous shareable maps and room leaderboards.

const J = (obj, status = 200, extraHeaders = {}) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...extraHeaders },
  });
const bad = (msg, status = 400) => J({ error: msg }, status);

const enc = (s) => new TextEncoder().encode(s);
const toHex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
const fromHex = (h) => new Uint8Array(h.match(/.{1,2}/g).map((x) => parseInt(x, 16)));

function rid(n = 8) {
  const a = new Uint8Array(n);
  crypto.getRandomValues(a);
  const abc = '0123456789abcdefghijklmnopqrstuvwxyz';
  return [...a].map((b) => abc[b % 36]).join('');
}
function randHex(n = 32) {
  const a = new Uint8Array(n);
  crypto.getRandomValues(a);
  return toHex(a);
}

// ---- passwords (PBKDF2-SHA256) ----
const PBKDF2_ITERS = 100000; // Cloudflare Workers caps PBKDF2 iterations at 100000
async function pbkdf2(pw, saltBytes) {
  const key = await crypto.subtle.importKey('raw', enc(pw), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt: saltBytes, iterations: PBKDF2_ITERS, hash: 'SHA-256' },
    key,
    256
  );
  return toHex(bits);
}
async function hashPassword(pw) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  return { hash: await pbkdf2(pw, salt), salt: toHex(salt) };
}
async function verifyPassword(pw, saltHex, hashHex) {
  const h = await pbkdf2(pw, fromHex(saltHex));
  if (h.length !== hashHex.length) return false;
  let diff = 0;
  for (let i = 0; i < h.length; i++) diff |= h.charCodeAt(i) ^ hashHex.charCodeAt(i);
  return diff === 0;
}

// ---- validation ----
function calcScore(data) {
  const sc = String(data || '').split('-')[0] || '';
  let s = 0;
  for (const ch of sc) {
    const n = +ch;
    if (n >= 0 && n <= 5) s += n;
  }
  return s;
}
const validData = (d) => typeof d === 'string' && d.length <= 200 && /^[0-5]{1,47}(-[0-9a-z]{1,47})?$/.test(d);
const cleanName = (s) => (typeof s === 'string' ? s : '').trim().slice(0, 40);
const validUser = (u) => typeof u === 'string' && /^[a-zA-Z0-9_.\-]{3,20}$/.test(u);
function cleanExtra(x) {
  // keep only known keys, bound size
  if (!x || typeof x !== 'object') return null;
  const out = {};
  if (x.memo && typeof x.memo === 'object') {
    out.memo = {};
    for (const k of Object.keys(x.memo).slice(0, 47)) out.memo[k] = String(x.memo[k] || '').slice(0, 500);
  }
  if (x.dates && typeof x.dates === 'object') {
    out.dates = {};
    for (const k of Object.keys(x.dates).slice(0, 47)) { const v = +x.dates[k]; if (v > 0) out.dates[k] = v; }
  }
  if (Array.isArray(x.ach)) out.ach = x.ach.filter((s) => typeof s === 'string').slice(0, 50);
  const s = JSON.stringify(out);
  return s.length <= 20000 ? s : null;
}

// ---- session cookie ----
const COOKIE = 'kk_sid';
const SESSION_TTL = 90 * 24 * 3600 * 1000;
function readCookie(request, name) {
  const raw = request.headers.get('cookie') || '';
  for (const part of raw.split(';')) {
    const [k, ...v] = part.trim().split('=');
    if (k === name) return v.join('=');
  }
  return null;
}
function sessionCookie(token, maxAgeSec) {
  return `${COOKIE}=${token}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${maxAgeSec}`;
}
async function currentUser(request, db) {
  const tok = readCookie(request, COOKIE);
  if (!tok) return null;
  const s = await db.prepare('SELECT user_id,expires FROM sessions WHERE token=?').bind(tok).first();
  if (!s || s.expires < Date.now()) return null;
  const u = await db.prepare('SELECT id,username FROM users WHERE id=?').bind(s.user_id).first();
  return u || null;
}

// upsert the logged-in user's board
async function saveUserMap(db, userId, body) {
  const name = cleanName(body.name);
  const data = body.data;
  const extra = cleanExtra(body.extra);
  const score = calcScore(data);
  const now = Date.now();
  const existing = await db.prepare('SELECT id FROM maps WHERE user_id=?').bind(userId).first();
  if (existing) {
    await db
      .prepare('UPDATE maps SET name=?,data=?,extra=?,score=?,updated_at=? WHERE id=?')
      .bind(name, data, extra, score, now, existing.id)
      .run();
    return { id: existing.id, score };
  }
  const id = rid(8), editKey = rid(16);
  await db
    .prepare('INSERT INTO maps(id,edit_key,user_id,name,data,extra,score,updated_at) VALUES(?,?,?,?,?,?,?,?)')
    .bind(id, editKey, userId, name, data, extra, score, now)
    .run();
  return { id, score };
}

export async function onRequest(context) {
  const { request, env, params } = context;
  const db = env.DB;
  const seg = Array.isArray(params.path) ? params.path : params.path ? [params.path] : [];
  const m = request.method;
  const now = () => Date.now();

  try {
    // ================= auth =================
    if (seg[0] === 'auth') {
      if (seg[1] === 'register' && m === 'POST') {
        const b = await request.json().catch(() => ({}));
        if (!validUser(b.username)) return bad('username: 3-20 chars a-z 0-9 _ . -');
        if (typeof b.password !== 'string' || b.password.length < 6) return bad('password: min 6 chars');
        const exists = await db.prepare('SELECT id FROM users WHERE username=?').bind(b.username).first();
        if (exists) return bad('username taken', 409);
        const { hash, salt } = await hashPassword(b.password);
        const id = rid(10);
        await db
          .prepare('INSERT INTO users(id,username,pass_hash,salt,created_at) VALUES(?,?,?,?,?)')
          .bind(id, b.username, hash, salt, now())
          .run();
        const token = randHex(32);
        await db.prepare('INSERT INTO sessions(token,user_id,expires) VALUES(?,?,?)').bind(token, id, now() + SESSION_TTL).run();
        return J({ username: b.username }, 200, { 'set-cookie': sessionCookie(token, SESSION_TTL / 1000) });
      }
      if (seg[1] === 'login' && m === 'POST') {
        const b = await request.json().catch(() => ({}));
        const u = await db.prepare('SELECT id,username,pass_hash,salt FROM users WHERE username=?').bind(String(b.username || '')).first();
        if (!u || !(await verifyPassword(String(b.password || ''), u.salt, u.pass_hash))) return bad('wrong login or password', 401);
        const token = randHex(32);
        await db.prepare('INSERT INTO sessions(token,user_id,expires) VALUES(?,?,?)').bind(token, u.id, now() + SESSION_TTL).run();
        return J({ username: u.username }, 200, { 'set-cookie': sessionCookie(token, SESSION_TTL / 1000) });
      }
      if (seg[1] === 'logout' && m === 'POST') {
        const tok = readCookie(request, COOKIE);
        if (tok) await db.prepare('DELETE FROM sessions WHERE token=?').bind(tok).run();
        return J({ ok: true }, 200, { 'set-cookie': `${COOKIE}=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0` });
      }
      return bad('not found', 404);
    }

    // ================= me (account board) =================
    if (seg[0] === 'me') {
      const user = await currentUser(request, db);
      if (!user) return bad('not authenticated', 401);
      if (m === 'GET') {
        const map = await db
          .prepare('SELECT id,name,data,extra,score,updated_at FROM maps WHERE user_id=?')
          .bind(user.id)
          .first();
        return J({ user: { username: user.username }, map: map || null });
      }
      if (m === 'PUT') {
        const b = await request.json().catch(() => ({}));
        if (!validData(b.data)) return bad('bad data');
        const r = await saveUserMap(db, user.id, b);
        return J(r);
      }
      return bad('method', 405);
    }

    // ================= map (anonymous shareable) =================
    if (seg[0] === 'map') {
      if (seg.length === 1 && m === 'POST') {
        const b = await request.json().catch(() => ({}));
        if (!validData(b.data)) return bad('bad data');
        const id = rid(8), editKey = rid(16), score = calcScore(b.data);
        await db
          .prepare('INSERT INTO maps(id,edit_key,name,data,score,updated_at) VALUES(?,?,?,?,?,?)')
          .bind(id, editKey, cleanName(b.name), b.data, score, now())
          .run();
        return J({ id, editKey, score });
      }
      const id = seg[1];
      if (!id) return bad('no id');
      if (m === 'GET') {
        const row = await db.prepare('SELECT id,name,data,extra,score,updated_at FROM maps WHERE id=?').bind(id).first();
        if (!row) return bad('not found', 404);
        return J(row);
      }
      if (m === 'PUT') {
        const b = await request.json().catch(() => ({}));
        if (!validData(b.data)) return bad('bad data');
        const key = request.headers.get('x-edit-key') || '';
        const row = await db.prepare('SELECT edit_key FROM maps WHERE id=?').bind(id).first();
        if (!row) return bad('not found', 404);
        if (row.edit_key !== key) return bad('forbidden', 403);
        const score = calcScore(b.data);
        await db.prepare('UPDATE maps SET name=?,data=?,score=?,updated_at=? WHERE id=?').bind(cleanName(b.name), b.data, score, now(), id).run();
        return J({ id, score });
      }
      return bad('method', 405);
    }

    // ================= room (leaderboards) =================
    if (seg[0] === 'room') {
      if (seg.length === 1 && m === 'POST') {
        const b = await request.json().catch(() => ({}));
        const id = rid(6);
        await db.prepare('INSERT INTO rooms(id,name,created_at) VALUES(?,?,?)').bind(id, cleanName(b.name), now()).run();
        return J({ id });
      }
      const id = seg[1];
      if (!id) return bad('no id');
      if (seg[2] === 'join' && m === 'POST') {
        const b = await request.json().catch(() => ({}));
        const mapId = String(b.mapId || '');
        const room = await db.prepare('SELECT id FROM rooms WHERE id=?').bind(id).first();
        if (!room) return bad('room not found', 404);
        const map = await db.prepare('SELECT id FROM maps WHERE id=?').bind(mapId).first();
        if (!map) return bad('map not found', 404);
        await db.prepare('INSERT OR IGNORE INTO room_members(room_id,map_id,joined_at) VALUES(?,?,?)').bind(id, mapId, now()).run();
        return J({ ok: true });
      }
      if (seg.length === 2 && m === 'GET') {
        const room = await db.prepare('SELECT id,name FROM rooms WHERE id=?').bind(id).first();
        if (!room) return bad('not found', 404);
        const { results } = await db
          .prepare(
            `SELECT m.id,m.name,m.score,m.updated_at
             FROM room_members rm JOIN maps m ON m.id=rm.map_id
             WHERE rm.room_id=? ORDER BY m.score DESC, m.updated_at ASC`
          )
          .bind(id)
          .all();
        return J({ id: room.id, name: room.name, members: results || [] });
      }
      return bad('method', 405);
    }

    return bad('not found', 404);
  } catch (e) {
    return J({ error: 'server', detail: String((e && e.message) || e) }, 500);
  }
}
