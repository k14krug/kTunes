from calendar import c
import xml.etree.ElementTree as ET
import sqlite3
import urllib.parse

#  Connects to db
conn = sqlite3.connect('iTunes.2.0.sqlite')
cur = conn.cursor()



# Function that finds the value in key and returns its text
# If value in key is blank, returns 'Unkown' as value
def lookup(i, key):
    found = False
    for child in i:
        if found : return child.text
        if child.tag == 'key' and child.text == key:
            found = True
    return 'Unkown'

doc = 'iTunesMusicLibrary.xml'
library = ET.parse(doc)
songs = library.findall('dict/dict/dict') #Finds all the songs in the 2nd child dict

# Variable for song count
song_count = 0

# Loops through and enters into db all songs in doc
for entry in songs:
    # Uses the lookup function to return the text from key
    name = lookup(entry, 'Name')
    artist = lookup(entry, 'Artist')
    album = lookup(entry, 'Album')
    genre = lookup(entry, 'Genre')
    length = lookup(entry, 'Total Time')
    year = lookup(entry, 'Year')
    count = lookup(entry, 'Play Count')
    rating = lookup(entry, 'Rating')
    last_play_dt = lookup(entry, 'Play Date UTC')
    #The following performs two functions
    # 1 - Takes the UTF-8 characters in the URL (like %20 for space) and converts it back to real characters
    # 2 - Removes th string file://localhost/
    location = urllib.parse.unquote(lookup(entry, 'Location')).replace("file://localhost/","")

    cur.execute('''INSERT OR REPLACE INTO Track
        (song, artist,  album, genre, length, last_play_dt, count, rating, location ) 
        VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ? )''', 
        (name, artist, album,  genre, length, last_play_dt, count, rating, location))

    cur.execute('''INSERT OR REPLACE INTO Tracks
        (song, artist,  album, genre, length, last_play_dt, cnt, rating, location ) 
        VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ? )''', 
        (name, artist, album,  genre, length, last_play_dt, count, rating, location))

    song_count += 1

cur.execute('''update track set genre = 'Latest'
              where genre like 'latest%' COLLATE NOCASE
            ''')
cur.execute('''update track set genre = 'In Rot'
              where genre like 'In rotation%' COLLATE NOCASE
            ''')
cur.execute('''update track set genre = 'Other'
              where genre like 'Other than New%' COLLATE NOCASE
            ''')
cur.execute('''update track set genre = 'Old'
              where genre like 'Old%' COLLATE NOCASE
            ''')
cur.execute('''update track set genre = 'Album'
              where genre like 'Album%' COLLATE NOCASE
            ''')

cur.execute('''update tracks set genre = 'Latest'
              where genre like 'latest%' COLLATE NOCASE
            ''')
cur.execute('''update tracks set genre = 'In Rot'
              where genre like 'In rotation%' COLLATE NOCASE
            ''')
cur.execute('''update tracks set genre = 'Other'
              where genre like 'Other than New%' COLLATE NOCASE
            ''')
cur.execute('''update tracks set genre = 'Old'
              where genre like 'Old%' COLLATE NOCASE
            ''')
cur.execute('''update tracks set genre = 'Album'
              where genre like 'Album%' COLLATE NOCASE
            ''')

# Python truncate optimizer
cur.execute('''delete from Latest_Tracks''')
cur.execute('''delete from In_Rot_Tracks''')
cur.execute('''delete from Other_Tracks''')
cur.execute('''delete from Old_Tracks''')
cur.execute('''delete from Album_Tracks''')

cur.execute('''insert into Latest_Tracks
               (song, artist, last_play_dt, rating, length, repeat_cnt, location)
               select song, artist, last_play_dt, rating, length, 1, location
                from track where genre = 'Latest'
                order by last_play_dt desc;
            ''')
cur.execute('''insert into In_Rot_Tracks
               (song, artist, last_play_dt, rating, length, repeat_cnt, location)
               select song, artist, last_play_dt, rating, length, 1, location
                from track where genre = 'In Rot'
                order by last_play_dt desc;
            ''')
cur.execute('''insert into Other_Tracks
               (song, artist, last_play_dt, rating, length, repeat_cnt, location)
               select song, artist, last_play_dt, rating, length, 1, location
                from track where genre = 'Other'
                order by last_play_dt desc;
            ''')
cur.execute('''insert into Old_Tracks
               (song, artist, last_play_dt, rating, length, repeat_cnt, location)
               select song, artist, last_play_dt, rating, length, 1, location
                from track where genre = "Old"
                order by last_play_dt desc;
            ''')
cur.execute('''insert into Album_Tracks
               (song, artist, last_play_dt, rating, length, repeat_cnt, location)
               select song, artist, last_play_dt, rating, length, 1, location
                from track where genre = 'Album'
                order by last_play_dt desc;
            ''')


# Load artist_last_played.
# This table is used during the merge to check the last time an artist has been
# Played and then checked against the hard code values for artist/genre replay cnt
#conn.commit()
#exit()
cur.execute('''insert into artist_last_played
        (artist, last_played, genre)
 select artist, 0, genre
   from tracks
 group by artist, genre''')


#cur.execute('''SELECT lower(artist), genre, count(*) 
#                 FROM tracks 
#                group by lower(artist), genre 
#                order by 2,1
#            ''')
#rows = cur.fetchall()
#for row in rows:
#      print(row)

#Ends transaction and make permanent all changes performed in the transaction

conn.commit()

# Prints out how many songs found compaired to songs entered into db
print('Found {} songs in {}.'.format((len(songs)), doc))
print('{} songs entered into the database.'.format(song_count))
