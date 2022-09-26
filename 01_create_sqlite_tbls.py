import sqlite3

conn = sqlite3.connect('iTunes.2.0.sqlite')
cur = conn.cursor()


# Makes new tables in db
cur.executescript('''
DROP TABLE IF EXISTS Artist;
DROP TABLE IF EXISTS Album;
DROP TABLE IF EXISTS Track;
DROP TABLE IF EXISTS Genre;
DROP TABLE IF EXISTS Artist_last_played;
DROP TABLE IF EXISTS Latest_Tracks;
DROP TABLE IF EXISTS In_Rot_tracks;
DROP TABLE IF EXISTS Other_Tracks;
DROP TABLE IF EXISTS Old_tracks;
DROP TABLE IF EXISTS Album_Tracks;

CREATE TABLE Artist_last_played (
    artist  TEXT,
    song_cnt integer,
    last_played INTEGER,
    genre TEXT,
    UNIQUE(artist,genre)
);

CREATE TABLE Track (
    id  INTEGER NOT NULL PRIMARY KEY 
        AUTOINCREMENT UNIQUE,
    song TEXT,
    artist TEXT, 
    album text,
    genre text,
    length INTEGER,
    last_play_dt DATE, 
    count INTEGER,
    rating INTEGER,
    location TEXT
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

CREATE TABLE Latest_Tracks (
    song TEXT,
    artist TEXT,
    last_play_dt DATE,
    last_played INTEGER DEFAULT 0,
    rating INTEGER,
    length INTEGER,
    repeat_cnt INTEGER,
    location TEXT
);

CREATE TABLE In_Rot_Tracks (
    song TEXT,
    artist TEXT,
    last_play_dt DATE,
    last_played INTEGER DEFAULT 0,
    rating INTEGER,
    length INTEGER,
    repeat_cnt INTEGER,
    location TEXT
);

CREATE TABLE Other_Tracks (
    song TEXT,
    artist TEXT,
    last_play_dt DATE,
    last_played INTEGER DEFAULT 0,
    rating INTEGER,
    length INTEGER,
    repeat_cnt INTEGER,
    location TEXT
);

CREATE TABLE Old_Tracks (
    song TEXT,
    artist TEXT,
    last_play_dt DATE,
    last_played INTEGER DEFAULT 0,
    rating INTEGER,
    length INTEGER,
    repeat_cnt INTEGER,
    location TEXT
);

CREATE TABLE Album_Tracks (
    song TEXT,
    artist TEXT,
    last_play_dt DATE,
    last_played INTEGER DEFAULT 0,
    rating INTEGER,
    length INTEGER,
    repeat_cnt INTEGER,
    location TEXT
);

CREATE UNIQUE INDEX idx_track
    ON track (song, artist,location);



''')
conn.commit()
