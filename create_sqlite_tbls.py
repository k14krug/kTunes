import sqlite3

conn = sqlite3.connect('kTunes.sqlite')
cur = conn.cursor()


# Makes new tables in db
cur.executescript('''
DROP TABLE IF EXISTS Artist;
DROP TABLE IF EXISTS Album;
DROP TABLE IF EXISTS Genre;
DROP TABLE IF EXISTS Artist_last_played;

CREATE TABLE Artist_last_played (
    artist  TEXT,
    song_cnt integer,
    last_played INTEGER,
    cat TEXT,
    UNIQUE(artist,cat)
);

CREATE TABLE Tracks (
    song TEXT,
    artist TEXT, 
    album text,
    cat text,
    length INTEGER,
    last_play_dt DATE,
    date_added date,
    rating INTEGER,
    location TEXT,
    cnt INTEGER,
    repeat_cnt INTEGER,
    last_played INTEGER DEFAULT 0 
);

''')
conn.commit()
