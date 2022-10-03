import sqlite3

conn = sqlite3.connect('iTunes.2.0.sqlite')
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
    genre TEXT,
    UNIQUE(artist,genre)
);

CREATE TABLE Tracks (
    song TEXT,
    artist TEXT, 
    album text,
    genre text,
    length INTEGER,
    last_play_dt DATE,
    rating INTEGER,
    location TEXT,
    cnt INTEGER,
    repeat_cnt INTEGER,
    last_played INTEGER DEFAULT 0 
);

''')
conn.commit()