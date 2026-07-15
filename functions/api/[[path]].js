// Keikenchi MVP-2 API — Cloudflare Pages Functions + D1 (binding: DB)
// Rooms without login: a map has a public id + a secret edit_key.

const J = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });
const bad = (msg, status = 400) => J({ error: msg }, status);

// short url-safe id
function rid(n = 8) {
  const a = new Uint8Array(n);
  crypto.getRandomValues(a);
  const abc = '0123456789abcdefghijklmnopqrstuvwxyz';
  return [...a].map((b) => abc[b % 36]).join('');
}

// data = "<scores>-<counts>"; score = sum of score digits (0..5)
function calcScore(data) {
  const sc = String(data || '').split('-')[0] || '';
  let s = 0;
  for (const ch of sc) {
    const n = +ch;
    if (n >= 0 && n <= 5) s += n;
  }
  return s;
}
// basic sanity: scores are 0-5 digits, optional -<base36 counts>
const validData = (d) => typeof d === 'string' && d.length <= 200 && /^[0-5]{1,47}(-[0-9a-z]{1,47})?$/.test(d);
const cleanName = (s) => (typeof s === 'string' ? s : '').trim().slice(0, 40);

export async function onRequest(context) {
  const { request, env, params } = context;
  const db = env.DB;
  const seg = Array.isArray(params.path) ? params.path : params.path ? [params.path] : [];
  const m = request.method;
  const now = () => Date.now();

  try {
    // ---- /api/map ----
    if (seg[0] === 'map') {
      // POST /api/map  -> create
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
      // GET /api/map/:id -> read
      if (m === 'GET') {
        const row = await db.prepare('SELECT id,name,data,score,updated_at FROM maps WHERE id=?').bind(id).first();
        if (!row) return bad('not found', 404);
        return J(row);
      }
      // PUT /api/map/:id -> update (needs x-edit-key)
      if (m === 'PUT') {
        const b = await request.json().catch(() => ({}));
        if (!validData(b.data)) return bad('bad data');
        const key = request.headers.get('x-edit-key') || '';
        const row = await db.prepare('SELECT edit_key FROM maps WHERE id=?').bind(id).first();
        if (!row) return bad('not found', 404);
        if (row.edit_key !== key) return bad('forbidden', 403);
        const score = calcScore(b.data);
        await db
          .prepare('UPDATE maps SET name=?,data=?,score=?,updated_at=? WHERE id=?')
          .bind(cleanName(b.name), b.data, score, now(), id)
          .run();
        return J({ id, score });
      }
      return bad('method', 405);
    }

    // ---- /api/room ----
    if (seg[0] === 'room') {
      // POST /api/room -> create room
      if (seg.length === 1 && m === 'POST') {
        const b = await request.json().catch(() => ({}));
        const id = rid(6);
        await db.prepare('INSERT INTO rooms(id,name,created_at) VALUES(?,?,?)').bind(id, cleanName(b.name), now()).run();
        return J({ id });
      }
      const id = seg[1];
      if (!id) return bad('no id');
      // POST /api/room/:id/join -> add a map to room
      if (seg[2] === 'join' && m === 'POST') {
        const b = await request.json().catch(() => ({}));
        const mapId = String(b.mapId || '');
        const room = await db.prepare('SELECT id FROM rooms WHERE id=?').bind(id).first();
        if (!room) return bad('room not found', 404);
        const map = await db.prepare('SELECT id FROM maps WHERE id=?').bind(mapId).first();
        if (!map) return bad('map not found', 404);
        await db
          .prepare('INSERT OR IGNORE INTO room_members(room_id,map_id,joined_at) VALUES(?,?,?)')
          .bind(id, mapId, now())
          .run();
        return J({ ok: true });
      }
      // GET /api/room/:id -> leaderboard
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
    return J({ error: 'server', detail: String(e && e.message || e) }, 500);
  }
}
