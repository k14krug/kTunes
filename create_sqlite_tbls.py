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

CREATE UNIQUE INDEX idx_artist_genre 
ON Artist_last_played (artist,genre);

CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song TEXT,
    artist TEXT, 
    album text,
    location TEXT,
    genre text,
    length INTEGER,
    last_play_dt DATE,
    date_added date,
    rating INTEGER,
    play_cnt INTEGER,
    category TEXT,
    recent_add_subcat INTEGER DEFAULT 0,
    cat_cnt INTEGER DEFAULT 0,
    artist_cat_cnt INTEGER DEFAULT 0,
    played_sw INTEGER DEFAULT 0
);

CREATE UNIQUE INDEX idx_song_artist 
ON tracks (song, artist,location);

CREATE TABLE Playlist (
    playlist_dt DATE,
    playlist_nm TEXT, 
    length INTEGER,
    nbr_of_songs INTEGER,
    recentadd_play_cnt DATE,
    debug_level TEXT,
    category TEXT,
    pct INTEGER,
    nbr_of_cat_songs INTEGER,
    nbr_of_cat_playlist_songs INTEGER
);

CREATE UNIQUE INDEX idx_playlist
ON playlist (playlist_dt, playlist_nm);


CREATE TABLE Playlist_tracks (
    playlist_dt DATE,
    playlist_nm TEXT,
    track_cnt INTEGER,
    artist TEXT, 
    song TEXT,
    category TEXT,
    length INTEGER,
    play_cnt INTEGER,
    last_play_dt DATE,
    cat_cnt INTEGER,
    artist_cat_cnt INTEGER
);

CREATE UNIQUE INDEX idx_playlist_tracks
ON playlist_tracks (playlist_dt, playlist_nm, track_cnt, artist, song);

''')
conn.commit()
