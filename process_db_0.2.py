from operator import truediv
from telnetlib import theNULL
import xml.etree.ElementTree as ET
import sqlite3
import array
import traceback
import sys

debug_level=0
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
  #print(debug_level, write_debug_to_file)
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
print("Tot songs for ",tot_nbr_of_minutes,"is", tot_nbr_of_songs)


# # # #
# Distinct Artist per genre (Based on entire lib of 3600 songs)
# Latest - 78 of 91
# In Rot - 279 of 540
# Other  - 503 1332
# Old    - 264 of 980
# Album  - 68 of 579
# # # # #
latest_repeat=15
in_rot_repeat=15
other_repeat=30
old_repeat=45
album_repeat=45

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

def load_arrays(genre, xx):
    a=genre
    b=xx
    track_list=[a,b]
    #track_array=array("u",track_list)
    print(track_list)


#if tot_eq_latest<=tot_eq_in_rot & tot_eq_latest <=tot_eq_other & tot_eq_latest<=tot_eq_old & tot_eq_latest<=tot_eq_album:
latest_cnt=0
in_rot_cnt=0
other_cnt=0
old_cnt=0
album_cnt=0


def compare_genre(genre_amt):
    x=genre_amt
    #print("         inside compare_genre", x,tot_eq_in_rot)
    #if x<=tot_eq_latest:
    if x<=tot_eq_latest and x<=tot_eq_in_rot and x<=tot_eq_other and x<=tot_eq_old and x<=tot_eq_album:
        #print("True")
        return True
 
#print("before if ",tot_eq_latest,tot_eq_in_rot, tot_eq_other, tot_eq_old, tot_eq_album)

# # # # # # # #
# This lays out the order of tracks based on the correct genre spacing to insure the right nbr
# of tracks for each genre are included. The calculation was first conceived in a spreasheet then
# translated into this code.
# 
# This is written to a file. Later in the program, the file is later read back in
# to place the appropriate song with that genre
#
# I wrote this very early in my python learning and not comfortable with variable scope so not sure if I really
# need to use the genre_amt variable to pass to compare_genre without impacting all genre amounts.
# # # # # # # #
def check_a_row():
    global tot_eq_latest,tot_eq_in_rot,tot_eq_other,tot_eq_old,tot_eq_album
    global latest_cnt, in_rot_cnt, other_cnt, album_cnt, old_cnt
    genre_amt=tot_eq_latest
    if compare_genre(genre_amt) == True:
      latest_cnt=latest_cnt+1
      tot_eq_latest=tot_eq_latest+eq_latest
      return_val="Latest"
    else:
      genre_amt=tot_eq_in_rot
      if compare_genre(genre_amt) == True:
        in_rot_cnt=in_rot_cnt+1
        tot_eq_in_rot=tot_eq_in_rot+eq_in_rot
        return_val="In Rot"
      else:
        genre_amt=tot_eq_other
        if compare_genre(genre_amt) == True:
          other_cnt=other_cnt+1
          tot_eq_other=tot_eq_other+eq_other
          return_val="Other"
        else:
          genre_amt=tot_eq_old
          if compare_genre(genre_amt) == True:
            old_cnt=old_cnt+1
            tot_eq_old=tot_eq_old+eq_old
            return_val="Old"
          else:
            genre_amt=tot_eq_album
            if compare_genre(genre_amt) == True:
              album_cnt=album_cnt+1
              tot_eq_album=tot_eq_album+eq_album
              return_val="Album"
    return return_val# tot_eq_latest,tot_eq_in_rot,tot_eq_other,tot_eq_old,tot_eq_album,in_rot_cnt

# # # # # # # # # # # #
# Write file with entery for every track with the proper genre set.
# # # # # # # # # # # #
f1 = open("process_db_genre_fin_order.txt", "w")
for x in range(0,tot_nbr_of_songs):
    f1.write(check_a_row()+'\n')
f1.close()

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
            #line1='#EXTINF: ' + str(length) + ',' + artist + " - " + song + '# ' +  genre + " : " + str(cnt)
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
          
          #print("  > after update artist_last_played ",artist, genre, cnt)
          return return_val
          
          # END check_artist_repeat


f2 = open("playlist.m3u", "w")
f2.write("#EXTM3U" + "\n")

latest_cur.execute('update latest_tracks set repeat_cnt = 1, last_played=0;')
in_rot_cur.execute('update in_rot_tracks set repeat_cnt = 1, last_played=0;')
other_cur.execute('update other_tracks set repeat_cnt = 1, last_played=0;')
old_cur.execute('update old_tracks set repeat_cnt = 1, last_played=0;')
album_cur.execute('update album_tracks set repeat_cnt = 1, last_played=0;')

def open_genre_track_cursors():
  debug_out(4,["open_genre_track_cursors:",cnt])
  latest_cur.execute('select * from latest_tracks where last_played <= ? order by last_play_dt',(cnt,))
  in_rot_cur.execute('select * from in_rot_tracks where last_played <= ? order by last_play_dt',(cnt,))
  other_cur.execute('select * from other_tracks where last_played <= ? order by last_play_dt',(cnt,))
  album_cur.execute('select * from album_tracks where last_played <= ? order by last_play_dt',(cnt,))
  old_cur.execute('select * from old_tracks where last_played <= ? order by last_play_dt',(cnt,))

cnt=0
open_genre_track_cursors()

# # # # # # # # 
# This function will be call repeatedly for one genre file rec until a track is found that meets the repeat rules.
# Based on the genre of the file rec it will select of record from the appropriate cursor. If it meets the repeat rules
# it will update that record last_played with 999999 to indicate it shouldn't be selected the next time the cursor is built.
# If it doesn't meet the repeat rule it will update last_played for all recs for that artist in this genre with
# artist_last_played plus the repeat interval. This will keep them from being included in the cursor until the loop count
# gets to the repeat interval. 
# # # # # # # # 
def fetch_genre_cur():
  global artist, length, song, location, genre_repeat, last_played, cnt
  return_val=False
  debug_out(2,["fetch_genre_cur:",cnt, genre,return_val])
  open_genre_track_cursors()
  if genre == 'Latest':
    # The latest genre is the smallest set of songs so its cursor can run out of
    # songs before completing the playlist. 
    # In that case the cursor fetch fails and you need to reexecute the cursor 
    # do start the fetch again
    try:
      song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=latest_cur.fetchone()
    except TypeError:
      debug_out(2,["fetch_genre_cur - Resetting last_played to 0 for all tracks:",cnt, genre,return_val])
      latest_cur.execute('update latest_tracks set last_played=0;')
      latest_cur.execute('select * from latest_tracks where last_played <= ? order by last_play_dt',(cnt,))
      song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=latest_cur.fetchone()

      #quit()
      
    genre_repeat=latest_repeat
    # continue to call check_artist_repeat till if finds a song passes the repeat test (typically only called once)
    if check_artist_repeat() == True:
      # We failed the artist repeat so set last_played so this artist won't be included till its time again
      
      latest_cur.execute('''update latest_tracks set last_played=?
                             where artist= ?
                               and last_played <> 999999;
                         ''',(artist_last_played+genre_repeat+1,artist))
      return_val=True
    else:
      latest_cur.execute('''update latest_tracks set last_played=999999
                             where song = ?
                               and artist= ?;
                         ''',(song,artist))
  if genre == 'In Rot':
    #print(" gotta In Rot rec")
    song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=in_rot_cur.fetchone() 
    genre_repeat=in_rot_repeat
    if check_artist_repeat() == True:
      # We failed the artist repeat so set last_played so this artist won't be included till its time again
      debug_out(2,["fetch_genre_cur - Failed check_artist_repeat:",cnt, genre,return_val,last_played])
      in_rot_cur.execute('''update in_rot_tracks set last_played=?
                             where artist= ?
                               and last_played <> 999999;
                         ''',(artist_last_played+genre_repeat+1,artist))
      in_rot_cur.execute('select * from in_rot_tracks where last_played <= ? order by last_play_dt',(cnt,))
      #in_rot_cur.execute('select * from in_rot_tracks where last_played <= ? order by last_play_dt',(cnt,))
      song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=in_rot_cur.fetchone() 
      debug_out(2,["fetch_genre_cur - after update last_played updated",cnt,artist,song,last_played])

      return_val=True
    else:
      debug_out(2,["fetch_genre_cur - Passed check_artist_repeat:",cnt, genre,return_val])
      in_rot_cur.execute('''update in_rot_tracks set last_played=999999
                             where song = ?
                               and artist= ?;
                         ''',(song,artist))
  if genre == 'Other':
    #print(" gotta Other rec")
    song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=other_cur.fetchone()
    #print(" Fetched",song,artist, last_play_dt, rating, length)
    genre_repeat=other_repeat
    if check_artist_repeat() == True:
      # We failed the artist repeat so set last_played so this artist won't be included till its time again
      other_cur.execute('''update other_tracks set last_played=?
                             where artist= ?
                               and last_played <> 999999;
                         ''',(artist_last_played+genre_repeat+1,artist))
      return_val=True
    else:
      other_cur.execute('''update other_tracks set last_played=999999
                             where song = ?
                               and artist= ?;
                         ''',(song,artist))
  if genre == 'Album':    
    song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=album_cur.fetchone()
    genre_repeat=album_repeat
    if check_artist_repeat() == True:
      # We failed the artist repeat so set last_played so this artist won't be included till its time again
      album_cur.execute('''update album_tracks set last_played=?
                             where artist= ?
                               and last_played <> 999999;
                         ''',(artist_last_played+genre_repeat+1,artist))
      return_val=True
    else:
      album_cur.execute('''update album_tracks set last_played=999999
                             where song = ?
                               and artist= ?;
                         ''',(song,artist))
  if genre == 'Old':
    song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=old_cur.fetchone()
    genre_repeat=old_repeat
    if check_artist_repeat() == True:
      # We failed the artist repeat so set last_played so this artist won't be included till its time again
      old_cur.execute('''update old_tracks set last_played=?
                             where artist= ?
                               and last_played <> 999999;
                         ''',(artist_last_played+genre_repeat+1,artist))
      return_val=True
    else:
      old_cur.execute('''update old_tracks set last_played=999999
                             where song = ?
                               and artist= ?;
                         ''',(song,artist))
  #if return_val == False:
  debug_out(2,["End fetch_genre_cur - return_val=",return_val])
  conn.commit
  if cnt == 47:
    return_val=False
  return(return_val)
# MAIN LOOP
# The process_db_genre_fin_order is an initialized version of the m3u file. Eash record
# is a place holder for the right genre track should be. Now need to find 
# the last recently played song for that genre and then make sure the artist
# doesn't fail the artist_last_played check.
with open(r"process_db_genre_fin_order.txt", 'r') as f1:
 for cnt, line in enumerate(f1):
  genre=line.strip()
  debug_out(1,["Main Loop:",cnt, genre])
  while fetch_genre_cur() == True:
    #pass
    debug_out(1,["End - Main Loop end"])

debug_out(1,["End of process_db_genre_file_order.txt. cnt=",cnt])

f1.close()
f2.close()

conn.commit()
conn.close()

#latest_cur.execute('select * from latest_tracks')
#in_rot_cur.execute('select * from in_rot_tracks')
#other_cur.execute('select * from other_tracks')
    

#song,artist, last_play_dt, rating, location=latest_cur.fetchone()
#print("Latest",song, artist, last_play_dt, rating, location)
#song,artist, last_play_dt, rating, location=other_cur.fetchone()
#print("Other",song, artist, last_play_dt, rating, location)


print("after fetchone")

# Prints out how many songs found compaired to songs entered into db
#print('Found {} songs in {}.'.format((len(songs)), doc))
#print('{} songs entered into the database.'.format(song_count))
