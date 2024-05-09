CREATE TABLE Artist_last_played (
    artist  TEXT,
    song_cnt integer,
    last_played INTEGER,
    genre TEXT,
    UNIQUE(artist,genre)
);

CREATE UNIQUE INDEX idx_artist_genre 
ON Artist_last_played (artist,genre);

CREATE TABLE sqlite_sequence(name,seq);

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
, username TEXT);

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
, artist_common_name TEXT, username TEXT);

CREATE TABLE Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
);
CREATE UNIQUE INDEX idx_playlist_tracks
ON playlist_tracks (username, playlist_dt, playlist_nm, track_cnt, artist, song);

CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song TEXT,
    artist TEXT, 
    album TEXT,
    location TEXT,
    genre TEXT,
    ktunes_genre text,
    ktunes_category TEXT,
    length INTEGER,
    last_play_dt DATE,
    date_added DATE,
    rating INTEGER,
    play_cnt INTEGER,
    cat_cnt INTEGER DEFAULT 0,
    artist_cat_cnt INTEGER DEFAULT 0,
    played_sw INTEGER DEFAULT 0,
    artist_common_name TEXT,
    ktunes_last_play_dt DATE,
    ktunes_play_cnt INTEGER
);

CREAT UNIQUE INDEX idx_song_artist 
ON tracks (song, artist,location);

CREATE UNIQUE INDEX idx_playlist
ON playlist (username, playlist_nm, category);

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
