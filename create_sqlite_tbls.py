import sqlite3
conn = sqlite3.connect('kTunes.sqlite')
cur = conn.cursor()


# Makes new tables in db
cur.executescript('''
DROP TABLE IF EXISTS Artist_last_played;
DROP TABLE IF EXISTS Tracks;
DROP TABLE IF EXISTS Playlist;

CREATE TABLE Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
);
                  
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
    artist_common_name TEXT,
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
    played_sw INTEGER DEFAULT 0,
    ktunes_last_play_dt DATE,
    ktunes_play_cnt INTEGER,
    ktunes_genre TEXT
                  
);

CREATE UNIQUE INDEX idx_song_artist 
ON tracks (song, artist,location);
                  
CREATE VIEW tracks_itunes 
   (id, 
    song, 
    artist, 
    artist_common_name, 
    location, 
    category,
    genre, 
    rating,
    last_play_dt, 
    play_cnt, 
    cat_cnt, 
    artist_cat_cnt, 
    played_sw) AS
SELECT 
    id,
    song,
    artist,
    artist_common_name,
    location,
    category,
    ktunes_genre,
    rating,
    last_play_dt,
    play_cnt,
    cat_cnt,
    artist_cat_cnt,
    played_sw
FROM tracks;

CREATE VIEW tracks_ktunes 
   (id, 
    song, 
    artist, 
    artist_common_name, 
    location, 
    category,
    genre, 
    rating,
    last_play_dt, 
    play_cnt, 
    cat_cnt, 
    artist_cat_cnt, 
    played_sw) AS
SELECT 
    id,
    song,
    artist,
    artist_common_name,
    location,
    category,
    ktunes_genre,
    rating,
    ktunes_last_play_dt,
    ktunes_play_cnt,
    cat_cnt,
    artist_cat_cnt,
    played_sw
FROM tracks;
                  
CREATE TABLE Playlist (
    username TEXT,
    playlist_type TEXT,
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
ON playlist (username, playlist_nm, category);


CREATE TABLE Playlist_tracks (
    username TEXT,
    playlist_dt DATE,
    playlist_nm TEXT,
    track_cnt INTEGER,
    artist TEXT, 
    artist_common_name TEXT,
    song TEXT,
    category TEXT,
    genre TEXT,
    length INTEGER,
    play_cnt INTEGER,
    last_play_dt DATE,
    cat_cnt INTEGER,
    artist_cat_cnt INTEGER
);
                  

CREATE UNIQUE INDEX idx_playlist_tracks
ON playlist_tracks (username, playlist_dt, playlist_nm, track_cnt, artist, song);

''')
conn.commit()
