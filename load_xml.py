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
  print("SQLite3" + DB + " does not exist and will be created.")
  creat_db="Yes"
  import create_sqlite_tbls
else:
  print("SQLite3" + DB + "already exist - skipping creation.")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Function that looks at an entry in the xml file and finds the value in key and returns its text
# If value in key is blank, returns 'Unknown' as value
def lookup(i, key):
    found = False
    for child in i:
        if found : return child.text
        if child.tag == 'key' and child.text == key:
            found = True
    return 'Unknown'

#cur.execute('''delete from Tracks;''')
#cur.execute('''delete from Artist_last_played;''')


doc = 'iTunesMusicLibrary.xml'
library = ET.parse(doc)
songs = library.findall('dict/dict/dict') #Finds all the songs in the 2nd child dict
# Variable for song count
song_count_xml = 0
song_count_inserts = 0
song_count_tbl_tot = 0
song_count_updates = 0

# Loops through and enters into db all songs in doc
for entry in songs:
    song_count_xml += 1
    # Uses the lookup function to return the text from key
    name = lookup(entry, 'Name')
    artist = lookup(entry, 'Artist')
    album = lookup(entry, 'Album')
    genre = lookup(entry, 'Genre')
    length = lookup(entry, 'Total Time')
    year = lookup(entry, 'Year')
    play_cnt = lookup(entry, 'Play Count')
    if play_cnt == 'Unknown':
      play_cnt = 0
    rating = lookup(entry, 'Rating')
    last_play_dt = lookup(entry, 'Play Date UTC')
    date_added = lookup(entry, 'Date Added')
    
    #The following performs two functions
    # 1 - Takes the UTF-8 characters in the URL (like %20 for space) and converts it back to real characters
    # 2 - Removes th string file://localhost/
    location = urllib.parse.unquote(lookup(entry, 'Location')).replace("file://localhost/","")
    
    # I did not use "insert or replace" because I want to capture the count of how many records are updated vs new inserts. 
    update = False
    data = [album, genre,genre, length,last_play_dt,rating,play_cnt,name,artist,location]
    try:
      cur.execute('''INSERT INTO tracks
          (song, artist,  album, location, genre, category, length, last_play_dt, date_added, rating, play_cnt) 
          VALUES ( ?, ?, ?, ?, ?,?, ?, ?, ?, ?, ? )''', 
          (name, artist, album, location, genre, genre, length, last_play_dt, date_added, rating, play_cnt))
    except:
      update = True
      #print('Updating track {}'.format([name, artist,last_play_dt]))
      cur.execute('''UPDATE tracks
              SET album        = ? ,
                  genre        = ? ,
                  category     = ? ,
                  length       = ? ,
                  last_play_dt = ? ,
                  rating       = ? ,
                  play_cnt     = ?  
              WHERE song     = ?
                AND artist   = ?
                AND location = ? ''',data)
      song_count_updates += 1    
    if update != True:
      song_count_inserts  += 1
    

# We use the iTunes genres column to create categories. 
# The creation of a category is based on the wild-carde, non-case sensitve values of genre
cur.execute('''update tracks set category = 'Latest'
              where genre like 'latest%' COLLATE NOCASE
            ''')
cur.execute('''update tracks set category = 'In Rot'
              where genre like 'In rotation%' COLLATE NOCASE
            ''')
cur.execute('''update tracks set category = 'Other'
              where genre like 'Other than New%' COLLATE NOCASE
            ''')
cur.execute('''update tracks set category = 'Old'
              where genre like 'Old%' COLLATE NOCASE
            ''')
cur.execute('''update tracks set category = 'Album'
              where genre like 'Album%' COLLATE NOCASE
            ''')


# Load artist_last_played.
# This table is used during the merge to check the last time an artist has been
# Played and then checked against the hard code values for artist/genre replay cnt.
# I want to keep track of this info from playlist to playlist 
# but info in this table is only based on the building of the last playlist. When I build 
# the next playlist I have no idea which songs of the last playlist were actually played. 
# Consider if I created on playlist and immediatly created a second playlist and used that 
# instead. This table would not reflect accurate play information. Just the info from creation 
# of the previous playlist
#conn.commit()
#exit()
# If there have been any new tracks added we need to insert them into artist last_played with a value of 0
  # (should this be moved to load_xml.py)

cur.execute('''insert into artist_last_played
               (artist, last_played, genre)
                select artist, 0, genre
                  from tracks
                where (artist,genre) not in 
                      (select  artist,genre from artist_last_played)
                group by artist, genre
           ''')
cur.execute('''select count(*) from tracks''')
row=cur.fetchone()
song_count_tbl_tot=row[0]
#Ends transaction and make permanent all changes performed in the transaction
conn.commit()
conn.close()

# Prints out how many songs found compaired to songs entered into db
print('Found {} songs in {}.'.format((len(songs)), doc))
print('{} songs entered into the database.'.format(song_count_inserts))
print('{} songs updated.'.format(song_count_updates))
print('kTunes DB now contains {} tracks.'.format(song_count_tbl_tot))

