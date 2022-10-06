from lib2to3.pgen2.pgen import DFAState
from operator import truediv
from telnetlib import theNULL
import xml.etree.ElementTree as ET
import sqlite3
import array
import traceback
import sys
from datetime import datetime,timedelta

spc = {}
spc[0] = ""
spc[1] = ""
spc[2] = " "
spc[3] = "  "
spc[4] = "   "
spc[5] = "    "

cnt=0
genre=""
create_recentadd_cat="No"
date_added=datetime.now() - timedelta(days=180)
playlist_name="playlist"

# Here we defines the genres were using and then start
# defining values to associate with them, like artist "repeat".
# The artist repeat is applied to each genre. For example we only want to here an artist
# from the Other genre no more frequently then every 30 songs (its the 3rd index in the list of genres).
genres=["RecentAdd","Latest","In Rot","Other","Old","Album"]
repeat = [15,15,15,30,45,45]
track_cnt=[0,0,0,0,0,0]

# Percentage of total tracks that a genre makes up. 
genre_pct=[str(0),str(50),str(20),str(10),str(10),str(10)]
playlist_length=1000
debug_level=0
write_debug_to_file = True

def debug_out(debug_val,debug_line):
    #print("debug val=",debug_val,"debug line",debug_line)
    if debug_val <= debug_level:
      i=0
      tupl = (debug_line)
      strg = spc[debug_val]
      for x in range(len(tupl)):
        item = str(tupl[x])
        strg = strg + item + " "
      if __name__ == "__main__":
    #    print("debug val=",debug_val,"debug line",debug_line)
        tupl_nbr_of_vals= len(tupl)
        if tupl_nbr_of_vals<5:
          for i in range(tupl_nbr_of_vals, 6):
            tupl=tupl + [" ",]
        frmt="{:<20s}{:>12s}{:>12s}{:>12s}{:>12s}"
        #print("tupl=",tupl,"frmt=",frmt)
        print(frmt.format(tupl[0],str(tupl[1]),str(tupl[2]),str(tupl[3]),str(tupl[4])))
      if write_debug_to_file == True:
        df.write(strg + "\n")
  
def main(dbug_lvl=debug_level,g_pct=genre_pct,playlist_nm=playlist_name,playlist_lgth=playlist_length,create_rcntadd_cat=create_recentadd_cat):  
  global df
  debug_level=dbug_lvl
  if write_debug_to_file == True:
    df = open("debug.log", "w")

  # Use the above percentages to determine how many songs from each genre to include in this playlist.
  print("create_rcntadd_cat=",create_rcntadd_cat)
  #exit()
  playlist_tot_songs=int(int(playlist_lgth)/4) # avg song is 4 minutes
  # 
  #  Connects to db
  conn = sqlite3.connect('kTunes.sqlite')

  sql_stmnt = conn.cursor()

  debug_out(1,["create_recently_added_genre:",date_added])
  if create_rcntadd_cat   == "Yes":
    sql_stmnt.execute('''update tracks set genre = 'RecentAdd'
                         where genre = 'Latest' COLLATE NOCASE
                           and date_added >= ?''',(date_added,))
  for x in range(len(genres)):
    sql_stmnt.execute('''select count(*) from tracks
                           where genre=?''',(genres[x],))
    row=sql_stmnt.fetchone()
    track_cnt[x]=row[0]
  if create_rcntadd_cat   == "Yes":
    #print("g_pct[] before",g_pct)
    #print("track_cnt[]",track_cnt)
    # Above we changed some of the latest tracks to recent add tracks. Now were going to determine
    # what percentage of each of those genres to use. We'll first come up with their percentages as
    # part of the original latest pct. For example, if the original latest pct was 50 and we now
    # have 10 recentadd tracks and 20 latest tracks then the recentadd percentages would be 50 * 10 / (10 +20)
    # Then well add a 20% preference to the recentadd % so these will play more freaquently 
    #          recent add preferecne * (orig latest pct * recentadd track cnt / (recentadd track cnt = latest_track cnt))
    orig_recentadd_pct = float(g_pct[1]) * track_cnt[0] / (track_cnt[0] + track_cnt[1])
    g_pct[0] = round(1.2 * float(g_pct[1]) * track_cnt[0] / (track_cnt[0] + track_cnt[1]))
    g_pct[1] = round(float(g_pct[1]) - float(g_pct[0]))
  else:
    g_pct[0] = 0

  #print("g_pct[] after",g_pct,"orig_recentadd_pct=",orig_recentadd_pct)
  #print("create_rcntadd_cat=",create_rcntadd_cat," Latest/recent %=",track_cnt[1], track_cnt[0], "gpct[0]=",g_pct[0], "gpct[1]=",g_pct[1])
 
  nbr_of_genre_songs= [round(playlist_tot_songs*float(g_pct[0])/100),
                      round(playlist_tot_songs*float(g_pct[1])/100),
                      round(playlist_tot_songs*float(g_pct[2])/100),
                      round(playlist_tot_songs*float(g_pct[3])/100),
                      round(playlist_tot_songs*float(g_pct[4])/100),
                      round(playlist_tot_songs*float(g_pct[5])/100)]
  
  # The eq list is used to compute the right spacing of genres in the playlist thus insuring it has the 
  # right number of tracks of each genre.
  print("nbr_of_genre_songs=",nbr_of_genre_songs)
  print("g_pct=",g_pct)
  print("playlist_tot_songs=",playlist_tot_songs)
  print("debug_lvl=",dbug_lvl)
  if create_rcntadd_cat   == "Yes":
    eq = [100/nbr_of_genre_songs[0],100/nbr_of_genre_songs[1], 100/nbr_of_genre_songs[2], 100/nbr_of_genre_songs[3],100/nbr_of_genre_songs[4],100/nbr_of_genre_songs[5]]
  else:
    eq = [0, 100/nbr_of_genre_songs[1],100/nbr_of_genre_songs[2], 100/nbr_of_genre_songs[3],100/nbr_of_genre_songs[4],100/nbr_of_genre_songs[5]]
  
  tot_eq = [eq[0],eq[1],eq[2],eq[3],eq[4],eq[5]]

  playlist_name=playlist_nm

  #if __name__ == "__main__":
  
 

  
  debug_out(1,["Resetting RecentAdd to Latest:",date_added])
  # If the RecentAdd switch had been set in an earlier run, need to switch back with this update
  sql_stmnt.execute('''update tracks set genre = 'Latest'
                         where genre = 'RecentAdd' COLLATE NOCASE''')

  genre_cur = conn.cursor()
  last_played_cur = conn.cursor()

  
  debug_out(0,["INFO","Plylst Lngth", playlist_lgth, "minutes."])
  debug_out(0,["INFO","Total Songs", playlist_tot_songs])
  debug_out(0,["INFO","Debug Level", debug_level])
  debug_out(0,["INFO","# # # # # # # # # # # # # # # # # # # # # "])
  debug_out(0,["INFO", "Genre","Pct",'PlylstSongs',"Tot Songs"])
  debug_out(0,["INFO", "----------","----",'-----------',"---------"])
  #exit()
  for x in range(len(genres)):
    debug_out(0,["INFO",genres[x],float(g_pct[x]),nbr_of_genre_songs[x],track_cnt[x]])

  # # # # # # # #
  # The check_a_row funcition lays out the order of tracks based on the correct genre spacing to insure the right nbr
  # of tracks for each genre are included. The calculation was first conceived in a spreasheet then
  # translated into this code.
  # 
  # This is written to a file. After its closed its opened for read so we can start finding tracks to match the genre
  #
  # This code seems to do the trick but I have not done any debuging with different ammounts of total tracks or changing
  # the genre percenatages to see if this would mess the formula up.
  # # # # # # # #
  def check_a_row():
    for x in range(5):
      amt=int(tot_eq[x])
      if amt<=tot_eq[0] and amt<=tot_eq[1] and amt<=tot_eq[2] and amt<=tot_eq[3] and amt<=tot_eq[4]:
          tot_eq[x]=tot_eq[x] + eq[x]
          debug_out(2,["check_a_row" , genres[x], tot_eq[x] ])
          break
    return_val=genres[x]
    debug_out(1,["check_a_row, genre=",genres[x]])
    return(return_val)

  # # # # # # # # # # # #
  # Write file with entery for every track with the proper genre set.
  # # # # # # # # # # # #
  f1 = open("process_db_genre_fin_order.txt", "w")
  for x in range(0,playlist_tot_songs):
      f1.write(check_a_row()+'\n')
  f1.close()

  # # # # # # # # # # # # # # # # # # 
  #
  #   Second part of program 
  #
  #   At this point the file has been written with the correct genre order, now it will
  #   be read back so we can create the m3u file with songs that match the genre
  #   But first we'll do some cleanup of the artist_last_played table
  # 
  # # # # # # # # # # # # # # # # # #

  sql_stmnt.execute('''delete from artist_last_played;''')

  sql_stmnt.execute('''insert into artist_last_played
                            (artist, last_played, genre)
                            select artist, 0, genre
                              from tracks
                          group by artist, genre;''')

  # # # # # # #
  # Determines if the current artist hasn't been played too recently based on 
  # Genre artist repeat interval
  # # # # # # # 
  def check_artist_repeat():
    global artist, artist_last_played,last_played
    debug_out(4,["check_artist_repeat:",artist,genre,cnt,last_played])
    last_played_cur.execute('''select g.last_played, genre, a.last_played
                                from artist_last_played  g
                                    ,(select max(last_played) last_played from artist_last_played 
                                      where artist=?) a
                                where artist=?
                                  and genre=?'''
                                ,(artist, artist,genre,))
    row=last_played_cur.fetchone()
    debug_out(4,[" Selected row from artist_last_played - ",row])
    
    if row is None:
      #Really Not sure why the above select would not return a row. The Artist_last_played
      #is loaded in load_sqlite.py based on all tracks so it should be good to go
      debug_out(0,"This shouldn't happen so I'm exiting - gonna have to debug this one")
      exit()
      insert_stmt='''insert into artist_last_played
                  (artist, genre, last_played)
                  values (?,?,?);''',(artist, genre, cnt)
      sql_stmnt.execute(insert_stmt,(artist,genre,cnt))
      conn.commit
    else:
      artist_genre_last_played = row[0]
      artist_last_played = row[2]
      debug_out(4,[artist," Loop cnt=",cnt," artist_genre_last_played=",artist_genre_last_played,"artist_last_played=",artist_last_played, genre,song, row])
      if artist_last_played == 0 or artist_last_played + genre_repeat < cnt:
        debug_out(5,["Valid track to write to playlist, row =",row])
        line1='#EXTINF: ' + str(length) + ',' + artist + " - " + song 
        f2.write(line1 + "\n")
        f2.write(location + "\n")
        if debug_level>0:
          f3.write(genre + "," + artist + " - " + song + "," + str(length) + "\n")
        artist_last_played=cnt+1
        sql_stmnt.execute('''update artist_last_played 
                                    set last_played = ?
                                  where artist = ?
                                    and genre = ?;''',(artist_last_played,artist,genre))
        return_val=False
      else:
        debug_out(5,["!! ",genre," Artist played too requently - should be skipped",artist_last_played])
        return_val=True
        
      conn.commit
      return return_val
  # END check_artist_repeat function

  def open_genre_track_cursors(genre):
    #This is the cursor of all the tracks for the genre we're trying to find a track for. 
    debug_out(4,["open_genre_track_cursors:",genre,cnt])

    genre_cur.execute('''select song, artist, last_play_dt, last_played, rating, length, repeat_cnt, location 
                            from tracks 
                          where genre = ? 
                            and last_played <= ? 
                            order by last_play_dt''',(genre,cnt,))

  # # # # # # # # 
  # This function will be called repeatedly for one genre file rec until a track is found that meets the repeat rules.
  # Based on the genre of the file rec, it will select the next track from the genre cursor. If it meets the repeat rules
  # it will update that record's last_played with 999999 to indicate it shouldn't be selected the next time the cursor is built.
  # If it doesn't meet the repeat rule it will update last_played for all recs for that artist in this genre with
  # artist_last_played plus the repeat interval. This will keep this artist from being included in the cursor until the 
  # loop count gets to the artist repeat interval. 
  # # # # # # # # 
  def process_genre_track(cnt):
    global artist, length, song, location, genre_repeat, last_played
    return_val=False
    debug_out(2,["process_genre_track:",cnt, genre,return_val])
    open_genre_track_cursors(genre)
    # If a genre doesn't have enough songs to match nbr_of_<genre>_songs then when we get to the end we need to reset that
    # genre and start from its beginning.
    try:
      song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=genre_cur.fetchone()
    except TypeError:
      debug_out(0,["INFO","Processed all", "'"+genre+"'", "tracks. Need to start over.","Cnt=", cnt, "return_val=",return_val])
      sql_stmnt.execute('update tracks set last_played=0 where genre = ?;',(genre,))
      open_genre_track_cursors(genre)
      song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=genre_cur.fetchone()
    
    genre_idx=genres.index(genre)
    genre_repeat=repeat[genre_idx]
    # continue to call check_artist_repeat till if finds a song that passes the repeat test 
    if check_artist_repeat() == True:
      # We failed the artist repeat so set last_played so this artist won't be included till its time again
      sql_stmnt.execute('''update tracks set last_played=?
                          where artist= ?
                              and genre = ?
                              and last_played <> 999999;
                        ''',(artist_last_played+genre_repeat+1,artist,genre))
      return_val=True
    else:
      # We found a valid track that can be added to the play list so update it in the tracks table so the song wont 
      # be eligible in the future
      sql_stmnt.execute('''update tracks set last_played=999999
                            where song = ?
                              and artist = ?
                              and genre = ?;
                        ''',(song,artist,genre))
    debug_out(2,["End process_genre_track - return_val=",return_val])
    conn.commit
  #  END OF FETCH_GENRE_CUR

  # MAIN LOOP
  # The process_db_genre_fin_order.txt file is an initialized version of the m3u file. Eash record
  # is a genre place holder for the right song track. Now need to find 
  # the last recently played song for that genre and then make sure the artist
  # doesn't fail the artist_last_played check and if all is good write it out to playlist.m3u

  f2 = open(playlist_name+".m3u", "w")
  f2.write("#EXTM3U" + "\n")
  f3 = open("playlist_debug.log", "w")
  

  # Since this is the "real" beginning of the script, need to initialize repeat_cnt and last_played.
  sql_stmnt.execute('update tracks set repeat_cnt = 1, last_played=0;')

  with open(r"process_db_genre_fin_order.txt", 'r') as f1:
   for cnt, line in enumerate(f1):
    genre=line.strip()
    debug_out(1,["Main Loop:",cnt, genre])
    while process_genre_track(cnt) == True:
      debug_out(1,"End - Main Loop")

  debug_out(1,["End of process_db_genre_file_order.txt. cnt=",cnt])

  conn.commit()
  conn.close()

  debug_out(0,["# # # # # # # # # # # # # # # # # # # # # "])
  debug_out(0,["# Script execution complete. Final track count=",cnt+1])
  debug_out(0,["# # # # # # # # # # # # # # # # # # # # # "])

  f1.close() # process_db_genre_fin_order.txt
  f2.close() # m3u file
  f3.close() # m3u file
  df.close() # Debug file

  return(playlist_tot_songs,nbr_of_genre_songs)

if __name__ == "__main__":
   main()
