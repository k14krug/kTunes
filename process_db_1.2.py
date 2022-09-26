from operator import truediv
from telnetlib import theNULL
import xml.etree.ElementTree as ET
import sqlite3
import array
import traceback
import sys

debug_level=1
write_debug_to_file = True
if write_debug_to_file == True:
  df = open("debug_out.txt", "w")
spc = {}
spc[1] = ""
spc[2] = " "
spc[3] = "  "
spc[4] = "   "
spc[5] = "    "

def debug_out(debug_val,debug_line):
  if debug_val <= debug_level:
    print(spc[debug_val],debug_line)
    if write_debug_to_file == True:
      tup1 = (debug_line)
      strg = spc[debug_val]
      for item in tup1:
        item = str(item)
        strg = strg + item + ", "
      df.write(strg + "\n")

tot_nbr_of_minutes=2500
tot_nbr_of_songs=int(tot_nbr_of_minutes/4)
print("Determining tracks for ",tot_nbr_of_minutes,"minutes of musics")
print("Total songs = ", tot_nbr_of_songs)
print("")
print("Debug Level - ",debug_level)
print("")


# # # #
# Distinct Artist per genre blased on entire lib of 3600 songs
# Latest - 78 of 91
# In Rot - 279 of 540
# Other  - 503 1332
# Old    - 264 of 980
# Album  - 68 of 579
# # # # #
cnt=0

# The repeat dictionary has the artist repeat value for each genre. For example we only want to here an artist
# from the Other genre no more frequently then every 30 songs.
repeat = {"Latest": 15,
          "In Rot": 15,
          "Other": 30,
          "Old":45,
          "Album":45}

genres=["Latest","In Rot","Other","Old","Album"]

# Percentage of total tracks that a genre makes up. This was derived from the original # My Radio # playlist
# and the percentages I found each genre was taking up.
latest_pct=.16
in_rot_pct=.44
other_pct=.27
old_pct=.08
album_pct=.05

# use the above percentages to determine how many songs from each genre to include in this playlist.
nbr_of_latest_songs=round(tot_nbr_of_songs*latest_pct)
nbr_of_in_rot_songs=round(tot_nbr_of_songs*in_rot_pct)
nbr_of_other_songs=round(tot_nbr_of_songs*other_pct)
nbr_of_old_songs=round(tot_nbr_of_songs*old_pct)
nbr_of_album_songs=round(tot_nbr_of_songs*album_pct)
print("Total 'Latest' songs - ",nbr_of_latest_songs)
print("Total 'In Rot' songs - ",nbr_of_in_rot_songs)
print("Total 'Other'  songs - ",nbr_of_other_songs)
print("Total 'Old'    songs - ",nbr_of_old_songs)
print("Total 'Album'  songs - ",nbr_of_album_songs)


# The *_eq_ variables are used to compute the right spacing of genres in the playlist thus insuring it has the 
# right number of tracks of each genre.
eq_latest=100/nbr_of_latest_songs
eq_in_rot=100/nbr_of_in_rot_songs
eq_other=100/nbr_of_other_songs
eq_album=100/nbr_of_album_songs
eq_old=100/nbr_of_old_songs

tot_eq_latest=eq_latest
tot_eq_in_rot=eq_in_rot
tot_eq_other=eq_other
tot_eq_album=eq_album
tot_eq_old=eq_old
 
#  Connects to db
conn = sqlite3.connect('iTunes.sqlite')

latest_cnt=0
in_rot_cnt=0
other_cnt=0
old_cnt=0
album_cnt=0

# # # # # # # # # # # #
# compare_genre
# Called from check_a_row. This is the basic formula to space out the genre correctly
def compare_genre(genre_amt):
    x=genre_amt
    if x<=tot_eq_latest and x<=tot_eq_in_rot and x<=tot_eq_other and x<=tot_eq_old and x<=tot_eq_album:
        return True
 

# # # # # # # #
# This lays out the order of tracks based on the correct genre spacing to insure the right nbr
# of tracks for each genre are included. The calculation was first conceived in a spreasheet then
# translated into this code.
# 
# This is written to a file. After its closed its opened for read so we can start finding tracks to match the genre
#
# This code seems to do the trick but I have not done any debuging with different ammounts of total tracks or changing
# the genre percenatages to see if this would mess the formula up.
# # # # # # # #
def check_a_row():
    global tot_eq_latest,tot_eq_in_rot,tot_eq_other,tot_eq_old,tot_eq_album
    genre_amt=tot_eq_latest
    #if compare_genre(genre_amt) == True:
    if genre_amt<=tot_eq_latest and genre_amt<=tot_eq_in_rot and genre_amt<=tot_eq_other and genre_amt<=tot_eq_old and genre_amt<=tot_eq_album:
      tot_eq_latest=tot_eq_latest+eq_latest
      return_val="Latest"
    else:
      genre_amt=tot_eq_in_rot
      #if compare_genre(genre_amt) == True:
      if genre_amt<=tot_eq_latest and genre_amt<=tot_eq_in_rot and genre_amt<=tot_eq_other and genre_amt<=tot_eq_old and genre_amt<=tot_eq_album:
        tot_eq_in_rot=tot_eq_in_rot+eq_in_rot
        return_val="In Rot"
      else:
        genre_amt=tot_eq_other
        #if compare_genre(genre_amt) == True:
        if genre_amt<=tot_eq_latest and genre_amt<=tot_eq_in_rot and genre_amt<=tot_eq_other and genre_amt<=tot_eq_old and genre_amt<=tot_eq_album:
          tot_eq_other=tot_eq_other+eq_other
          return_val="Other"
        else:
          genre_amt=tot_eq_old
          #if compare_genre(genre_amt) == True:
          if genre_amt<=tot_eq_latest and genre_amt<=tot_eq_in_rot and genre_amt<=tot_eq_other and genre_amt<=tot_eq_old and genre_amt<=tot_eq_album:
            tot_eq_old=tot_eq_old+eq_old
            return_val="Old"
          else:
            genre_amt=tot_eq_album
            #if compare_genre(genre_amt) == True:
            if genre_amt<=tot_eq_latest and genre_amt<=tot_eq_in_rot and genre_amt<=tot_eq_other and genre_amt<=tot_eq_old and genre_amt<=tot_eq_album:
              tot_eq_album=tot_eq_album+eq_album
              return_val="Album"
            else:
              print("we didn't find a value so exiting",genre_amt,tot_eq_latest, tot_eq_in_rot, tot_eq_other, tot_eq_old, tot_eq_album)
              exit()
    return return_val

# # # # # # # # # # # #
# Write file with entery for every track with the proper genre set.
# # # # # # # # # # # #
f1 = open("process_db_genre_fin_order.txt", "w")
for x in range(0,tot_nbr_of_songs):
    f1.write(check_a_row()+'\n')
f1.close()

# # # # # # # # # # # # # # # # # # 
#
#   Second part of program 
#
#   At this point the file has been written with the correct genre order, now it will
#   be read back so we can create the m3u file with songs that match the genre
#   First we'll do some cleanup of the artist_last_played table
# 
# # # # # # # # # # # # # # # # # #

genre_cur = conn.cursor()
sql_stmnt = conn.cursor()
latest_cur = conn.cursor()
in_rot_cur = conn.cursor()
other_cur = conn.cursor()
old_cur = conn.cursor()
album_cur = conn.cursor()

last_played_cur = conn.cursor()
last_played_cur.execute('''delete from artist_last_played;''')

last_played_cur.execute('''insert into artist_last_played
        (artist, last_played, genre)
 select artist, 0, genre
   from tracks
 group by artist, genre;''')

last_played_cur.execute('''delete from artist_last_played;''')

last_played_cur.execute('''insert into artist_last_played
        (artist, last_played, genre)
 select artist, 0, genre
   from track
 group by artist, genre;''')


# # # # # # #
# Determines if the current artist hasn't been played too recently based on 
# Genre repeat interval
# # # # # # # 
def check_artist_repeat():
  global artist, genre, artist_last_played,last_played
  debug_out(4,["check_artist_repeat:",artist,genre,cnt,last_played])
  last_played_cur.execute('''select g.last_played, genre, a.last_played
                              from artist_last_played  g
                                  ,(select max(last_played) last_played from artist_last_played 
                                     where artist=?) a
                              where artist=?
                                and genre=?'''
                              ,(artist, artist,genre,))
  #last_played, genre=last_played_cur.fetchone()
  row=last_played_cur.fetchone()
  debug_out(4,[" Selected row from artist_last_played - ",row])
  
  if row is None:
    #Really Not sure why the above select would not return a row. The Artist_last_played
    #Is loaded in load_sqlite.py based on all tracks so it should be good to go
    debug_out(4,"This shouldn't happen so I'm exiting - gonna have to debug this one")
    exit()
    insert_stmt='''insert into artist_last_played
                 (artist, genre, last_played)
                 values (?,?,?);''',(artist, genre, cnt)
    last_played_cur.execute(insert_stmt,(artist,genre,cnt))
    conn.commit
  else:
    artist_genre_last_played = row[0]
    artist_last_played = row[2]
    debug_out(4,[artist," Loop cnt=",cnt," artist_genre_last_played=",artist_genre_last_played,"artist_last_played=",artist_last_played, genre,song, row])
    if artist_last_played == 0 or artist_last_played + genre_repeat < cnt:
      line1='#EXTINF: ' + str(length) + ',' + artist + " - " + song 
      f2.write(line1 + "\n")
      f2.write(location + "\n")
      artist_last_played=cnt+1
      last_played_cur.execute('''update artist_last_played 
                                  set last_played = ?
                                where artist = ?
                                  and genre = ?;''',(artist_last_played,artist,genre))
      debug_out(5,["Valid track to write to playlist, row =",row])
      return_val=False
    else:
      debug_out(5,["!! ",genre," Artist played too requently - should be skipped",artist_last_played])
      return_val=True
      
    conn.commit
    return return_val
# END check_artist_repeat function


def open_genre_track_cursors(genre):
  debug_out(4,["open_genre_track_cursors:",genre,cnt])

  genre_cur.execute('''select song, artist, last_play_dt, last_played, rating, length, repeat_cnt, location 
                          from tracks 
                        where genre = ? 
                          and last_played <= ? 
                          order by last_play_dt''',(genre,cnt,))

# # # # # # # # 
# This function will be call repeatedly for one genre file rec until a track is found that meets the repeat rules.
# Based on the genre of the file rec it will select of record from the appropriate cursor. If it meets the repeat rules
# it will update that record last_played with 999999 to indicate it shouldn't be selected the next time the cursor is built.
# If it doesn't meet the repeat rule it will update last_played for all recs for that artist in this genre with
# artist_last_played plus the repeat interval. This will keep them from being included in the cursor until the loop count
# gets to the repeat interval. 
# # # # # # # # 
def fetch_genre_cur():
  global artist, length, song, location, genre_repeat, last_played, cnt, genre
  return_val=False
  debug_out(2,["fetch_genre_cur:",cnt, genre,return_val])
  open_genre_track_cursors(genre)
  #if genre == 'Latest':
  # If a genre doesn't have enough songs to match nbr_of_<genre>_songs then when we get to the end we need to reset that
  # genre and start from its beginning.
  try:
    song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=genre_cur.fetchone()
  except TypeError:
    debug_out(2,["fetch_genre_cur - Processed all genres tracks, need to start over ",cnt, genre, return_val])
    sql_stmnt.execute('update tracks set last_played=0 where genre = ?;',(genre,))
    open_genre_track_cursors(genre)
    song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=genre_cur.fetchone()
    
  genre_repeat=repeat[genre]
  # continue to call check_artist_repeat till if finds a song passes the repeat test (typically only called once)
  if check_artist_repeat() == True:
    # We failed the artist repeat so set last_played so this artist won't be included till its time again
    sql_stmnt.execute('''update tracks set last_played=?
                         where artist= ?
                            and genre = ?
                             and last_played <> 999999;
                       ''',(artist_last_played+genre_repeat+1,artist,genre))
    return_val=True
  else:
    # We found a valid track that can be added to the play list so update it in the tracks table so it wont be eligible in the future
    sql_stmnt.execute('''update tracks set last_played=999999
                           where song = ?
                             and artist = ?
                             and genre = ?;
                       ''',(song,artist,genre))
  debug_out(2,["End fetch_genre_cur - return_val=",return_val])
  conn.commit
#  END OF FETCH_GENRE_CUR

# MAIN LOOP
# The process_db_genre_fin_order.txt file is an initialized version of the m3u file. Eash record
# is a place holder for the right genre track should be. Now need to find 
# the last recently played song for that genre and then make sure the artist
# doesn't fail the artist_last_played check and if all is good write it out to playlist.m3u

f2 = open("playlist.m3u", "w")
f2.write("#EXTM3U" + "\n")


# Since this is the beginning of the script, need to initialize repeat_cnt and last_played.
sql_stmnt.execute('update tracks set repeat_cnt = 1, last_played=0;')

with open(r"process_db_genre_fin_order.txt", 'r') as f1:
 for cnt, line in enumerate(f1):
  genre=line.strip()
  debug_out(1,["Main Loop:",cnt, genre])
  while fetch_genre_cur() == True:
    #pass
    debug_out(1,"End - Main Loop")

debug_out(1,["End of process_db_genre_file_order.txt. cnt=",cnt])

f1.close()
f2.close()

conn.commit()
conn.close()

debug_out(1,"Thats a wrap!")