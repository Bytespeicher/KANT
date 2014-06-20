DROP TABLE IF EXISTS keys;
CREATE TABLE keys (
  id          INTEGER   PRIMARY KEY AUTOINCREMENT,
  name        TEXT      NOT NULL,
  user        INTEGER   NOT NULL,
  last_update DATETIME  DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY(user) REFERENCES user(id)
);

DROP TABLE IF EXISTS key_history;
CREATE TABLE key_history (
  id          INTEGER   PRIMARY KEY AUTOINCREMENT,
  key         INTEGER   NOT NULL,
  user_before INTEGER   NOT NULL,
  user_after  INTEGER   NOT NULL,
  name_before TEXT      NOT NULL,
  name_after  TEXT      NOT NULL,
  update_time DATETIME  DEFAULT CURRENT_TIMESTAMP,
  change_user INTEGER   NOT NULL,

  FOREIGN KEY(user_before) REFERENCES user(id),
  FOREIGN KEY(user_after)  REFERENCES user(id),
  FOREIGN KEY(change_user) REFERENCES user(id),
  FOREIGN KEY(key)         REFERENCES key(id)
);

DROP TABLE IF EXISTS users;
CREATE TABLE users (
  id        INTEGER   PRIMARY KEY AUTOINCREMENT,
  name      TEXT      NOT NULL,
  mail      TEXT      NOT NULL, 
  phone     INTEGER   NOT NULL
);

DROP TABLE IF EXISTS admins;
CREATE TABLE admins (
  id        INTEGER   PRIMARY KEY AUTOINCREMENT,
  name      TEXT      NOT NULL,
  password  TEXT      NOT NULL,
  mail      TEXT      NOT NULL
);

INSERT INTO admins (name,password,mail) VALUES ('admin', '$6$rounds=109454$C4Ips3OIMfXGvij2$6qCWMZziJ9/QHYxLejRtKQrTgL4s5EZDITrIm3nUdoXCuzGJu9iRenZ15dAyDTXsxpYLWiXdvw0Fn8IVIDJrv0', '');

DROP TABLE IF EXISTS config;
CREATE TABLE config (
  name      TEXT    PRIMARY KEY,
  value     TEXT
);

INSERT OR REPLACE INTO config (name, value) VALUES ('dbversion', '1');
