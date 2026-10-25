CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  kind TEXT NOT NULL,                 -- 'pack' | 'custom'
  status TEXT NOT NULL DEFAULT 'new', -- new | confirmed | deposit_paid | printing | ready | delivered | cancelled
  paid INTEGER NOT NULL DEFAULT 0,
  customer TEXT NOT NULL,
  phone TEXT NOT NULL,
  area TEXT,
  name TEXT,                          -- name printed on the pack
  theme TEXT,
  colours INTEGER,
  pieces TEXT,                        -- 'all' or tag|pencil|...
  price REAL,                         -- computed on the server
  qty INTEGER NOT NULL DEFAULT 1,
  details TEXT,                       -- free text (custom requests / notes)
  admin_note TEXT
);
CREATE INDEX IF NOT EXISTS orders_phone ON orders (phone, created_at);
