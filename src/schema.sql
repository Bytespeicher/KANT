DROP TABLE IF EXISTS keys;
CREATE TABLE keys (
  id          INTEGER   PRIMARY KEY AUTOINCREMENT,
  name        TEXT      NOT NULL,
  user        INTEGER   NOT NULL,
  last_update INTEGER   NOT NULL,

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
  update_time INTEGER   NOT NULL,
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
  password  TEXT      NOT NULL,
  mail      TEXT      NOT NULL, 
  phone     INTEGER   NOT NULL
);