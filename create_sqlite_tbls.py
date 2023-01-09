import sqlite3

conn = sqlite3.connect('kTunes.sqlite')
cur = conn.cursor()


# Makes new tables in db
cur.executescript('''
DROP TABLE IF EXISTS Artist_last_played;
DROP TABLE IF EXISTS Tracks;
DROP TABLE IF EXISTS Playlist;

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
    location TEXT,
    album text,
    genre text,
    length INTEGER,
    last_play_dt DATE,
    date_added date,
    rating INTEGER,
    cnt INTEGER,
    repeat_cnt INTEGER,
    last_played INTEGER DEFAULT 0 
);

CREATE UNIQUE INDEX idx_song_artist 
ON tracks (song, artist,location);

CREATE TABLE Playlist (
    playlist_dt DATE,
    playlist_nm TEXT, 
    length INTEGER,
    nbr_of_songs INTEGER,
    recentadd_dt DATE,
    debug_level TEXT,
    genre TEXT,
    pct INTEGER,
    nbr_of_genre_songs INTEGER,
    nbr_of_genre_playlist_songs INTEGER
);

CREATE TABLE Playlist_tracks (
    playlist_dt DATE,
    playlist_nm TEXT,
    track_cnt INTEGER,
    artist TEXT, 
    song TEXT,
    genre TEXT,
    length INTEGER,
    last_play_dt DATE,
    last_played INTEGER,
    repeat_cnt INTEGER
);
''')
conn.commit()
