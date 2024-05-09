from calendar import c
import xml.etree.ElementTree as ET
import sqlite3
from sqlite3 import IntegrityError
import urllib.parse
from os.path import isfile, getsize
import os
import time

#  This program loads the iTunesMusicLibrary.xml file into a SQLite3 database
#  The program will create the database if it does not exist
#  It will load/update the database with tracks data from the xml file

def main(xml_file):
   
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
      print("load_xml - SQLite3" + DB + " does not exist and will be created.")
      creat_db="Yes"
      import create_sqlite_tbls
    else:
      print("load_xml - " + DB + " already exist - skipping creation.")

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

    #Dictionary to return to calling program
    return_dict = {}

    # Get the current working directory
    current_directory = os.getcwd()

    # Combine the directory and file into a single path
    doc = os.path.join(current_directory, xml_file)
    return_dict['xml_file'] = doc

    # Get the last modified time
    last_modified_time = os.path.getmtime(doc)

    # Convert the timestamp to a readable format
    last_modified_date = time.ctime(last_modified_time)

    

    print(f"           {doc} last modified date: {last_modified_date}")
    return_dict['last_modified_date'] = last_modified_date



    library = ET.parse(doc)
    songs = library.findall('dict/dict/dict') #Finds all the songs in the 2nd child dict
    # Variable for song count
    song_count_inserts = 0
    song_count_tbl_tot = 0
    song_count_updates = 0

    # Loops through xml and insert/update tracks table
    for entry in songs:
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
              (song, artist,  artist_common_name, album, location, genre, category, ktunes_genre, length, last_play_dt, ktunes_last_play_dt, date_added, rating, play_cnt, ktunes_play_cnt) 
              VALUES ( ?, ?, ?, ?, ?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
              (name, artist, artist, album, location, genre, genre, genre, length, last_play_dt, last_play_dt, date_added, rating, play_cnt, play_cnt))
        except IntegrityError: #Row already exists so update it
          update = True
          #if artist.startswith('Phoe'):
          #print('Updating track {}'.format([name, artist, location]))

          # On an update we are not updating ktunes_last_play_dt or ktunes_play_cnt or ktunes_genre.
          # This is because the app will allows you to choose to create a playlist based on the native
          # iTunes data or the kTunes data. 
          cur.execute('''UPDATE tracks
                  SET album        = ? ,
                      genre        = ? ,
                      category = ? ,
                      length       = ? ,
                      last_play_dt = ? ,
                      rating       = ? ,
                      play_cnt     = ?  
                  WHERE song     = ?
                    AND artist   = ?
                    AND location = ? ''',data)
          song_count_updates += 1    
          #if artist.startswith('Phoe'):
          #cur.execute('''select * from tracks where artist like 'Phoeb%' ''')
          #row=cur.fetchone()
          #song_count_tbl_tot=row[0]
          #print('Updated track {}'.format([row]))
              
        except Exception as e:
          print(f"An error occurred: {e}")
          print('Error on track {}'.format([name, artist, location]))
          raise
         
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

    #cur.execute('''insert into artist_last_played
    #              (artist, last_played, genre)
    #                select artist, 0, genre
    #                  from tracks
    #                where (artist,genre) not in 
    #                      (select  artist,genre from artist_last_played)
    #                group by artist, genre
    #          ''')
    cur.execute('''select count(*) from tracks''')
    row=cur.fetchone()
    song_count_tbl_tot=row[0]
    #Ends transaction and make permanent all changes performed in the transaction
    conn.commit()
    conn.close()

    # Prints out how many songs found compaired to songs entered into db
    return_dict['status'] = 'success'

    print(f'           {len(songs)} songs in itunes library  {doc}')
    return_dict['song_count_xml'] = len(songs)
    print('           {} songs entered into the database.'.format(song_count_inserts))
    return_dict['song_count_inserts'] = song_count_inserts
    print('           {} songs updated.'.format(song_count_updates))
    print(f'           {song_count_tbl_tot} now in DB')
    return_dict['song_count_tbl_tot'] = song_count_tbl_tot
    #print(f"load_xml - {doc} last modified date: {last_modified_date}")

    #print('return_dict: ', return_dict)
    return(return_dict)
if __name__ == '__main__':
    main()

