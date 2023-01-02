from calendar import c
import xml.etree.ElementTree as ET
import sqlite3
import urllib.parse
from os.path import isfile, getsize

#  Connects to db
DB="kTunes.sqlite"


create_db="Yes"
if isfile(DB):    
  if getsize(DB) > 100:
        with open(DB,'r', encoding = "ISO-8859-1") as f:
            header = f.read(100)
            if header.startswith('SQLite format 3'):
              create_db="No"
if create_db == "Yes":
  print("SQLite3" + DB + "does not exist and will be created.")
  creat_db="Yes"
  import create_sqlite_tbls
else:
  print("SQLite3" + DB + "already exist - skipping createion.")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Function that finds the value in key and returns its text
# If value in key is blank, returns 'Unknown' as value
def lookup(i, key):
    found = False
    for child in i:
        if found : return child.text
        if child.tag == 'key' and child.text == key:
            found = True
    return 'Unknown'

cur.execute('''delete from Tracks;''')
cur.execute('''delete from Artist_last_played;''')


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
    date_added = lookup(entry, 'Date Added')
    
    #The following performs two functions
    # 1 - Takes the UTF-8 characters in the URL (like %20 for space) and converts it back to real characters
    # 2 - Removes th string file://localhost/
    location = urllib.parse.unquote(lookup(entry, 'Location')).replace("file://localhost/","")

    cur.execute('''INSERT OR REPLACE INTO Tracks
        (song, artist,  album, genre, length, last_play_dt, date_added, cnt, rating, location ) 
        VALUES ( ?, ?, ?, ?, ?,?, ?, ?, ?, ? )''', 
        (name, artist, album,  genre, length, last_play_dt, date_added, count, rating, location))

    song_count += 1


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


#Ends transaction and make permanent all changes performed in the transaction

conn.commit()
conn.close()

# Prints out how many songs found compaired to songs entered into db
print('Found {} songs in {}.'.format((len(songs)), doc))
print('{} songs entered into the database.'.format(song_count))
