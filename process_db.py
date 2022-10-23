from lib2to3.pgen2.pgen import DFAState
from nis import cat
from operator import truediv
from re import X
from telnetlib import theNULL
import xml.etree.ElementTree as ET
import sqlite3
import array
import traceback
import sys
from datetime import datetime,timedelta
#import debugpy

spc = {}
spc[0] = ""
spc[1] = ""
spc[2] = " "
spc[3] = "  "
spc[4] = "   "
spc[5] = "    "

cnt=0
cat=""
df=""

# Below are the default values for the parms passed into main.
# definable_cats are the genre values I use in my itunes catalog. Set these to values appropriate for your catalog.
# Next we set values to associate with them like percentage to include for each cat and artist "repeat".
# The artist repeat is applied to each cat, for example we only want to here an artist from the 2nd cat no more frequently then every 15 songs.
# The first index of c_pct and repeat are associated with the dynamic category; recent_add. The remaining indexes are associated with definable_cats.
debug_level=0
definable_cats = ["Latest","In Rot","Other","Old","Album"]
recentadd_cat = ["RecentAdd"] 
cats = recentadd_cat + definable_cats
c_pct=[str(0),str(50),str(20),str(10),str(10),str(10)]
repeat = [15,15,15,30,45,9]
playlist_name="playlist"
playlist_length=1000
create_recentadd_cat="No"
recentadd_date=datetime.now() - timedelta(days=180)
weightinc_pct=str(20)
create_playlist="Yes"

track_cnt=[0,0,0,0,0,0]
write_debug_to_file = True

def debug_out(debug_val,debug_line):
#    print("debug val=",debug_val,"debug line",debug_line)
    if debug_val <= debug_level:
      #Gi=0
      tupl = (debug_line)
      strg = spc[debug_val]
      x = strg + tupl[0]
      #print("debug val=",debug_val,"debug line",debug_line," tupl=",tupl,"tupl[0]=",tupl[0]," x=",x )
      
      tupl[0] = str(x)
      tupl_nbr_of_vals= len(tupl)
      if tupl_nbr_of_vals <= 11:
        for i in range(tupl_nbr_of_vals, 12):
          tupl=tupl + ["",]
      else:
         tupl[0] = "DEBUG ERROR" 
         tupl[1] = "Too many debug items to display"
         tupl[2] = debug_line
      frmt="{:<20s}{:<20s}{:<12s}{:<12s}{:<12s}{:<12s}{:<12s}{:<12s}{:<12s}"
      strg=frmt.format(tupl[0],str(tupl[1]),str(tupl[2]),str(tupl[3]),str(tupl[4]),str(tupl[5]),str(tupl[6]),str(tupl[7]),str(tupl[8]))
      #print("Length of debug_out line=",len(strg),debug_line)
      #if __name__ == "__main__":
      print(strg)
      if write_debug_to_file == True:
        df.write(strg + "\n")
        
def initialize_things():
  global  weightinc_pct, playlist_tot_songs, tot_eq, eq, sql_stmnt, cat_cursor, last_played_cur, conn, nbr_of_cat_songs

  # Use the above percentages to determine how many songs from each cat to include in this playlist.
  playlist_tot_songs=int(int(playlist_length)/4) # avg song is 4 minutes
  # 
  #  Connects to db
  conn = sqlite3.connect('kTunes.sqlite')

  sql_stmnt = conn.cursor()
  cat_cursor = conn.cursor()
  last_played_cur = conn.cursor()
  
  debug_out(1,["Resetting RecentAdd to Latest:",recentadd_date])
  # If the RecentAdd switch had been set in an earlier run, need to switch back with this update
  sql_stmnt.execute('''update tracks set cat = 'Latest'
                         where cat = 'RecentAdd' COLLATE NOCASE''')

  debug_out(1,["create_recently_added_cat:",recentadd_date])
  if create_recentadd_cat   == "Yes":
    sql_stmnt.execute('''update tracks set cat = 'RecentAdd'
                         where cat = 'Latest' COLLATE NOCASE
                           and date_added >= ?''',(recentadd_date,))

  # get track cound for each category
  for x in range(len(cats)):
    sql_stmnt.execute('''select count(*) from tracks
                           where cat=?''',(cats[x],))
    row=sql_stmnt.fetchone()
    track_cnt[x]=row[0]
  if create_recentadd_cat   == "Yes":
    #print("track_cnt[]",track_cnt)
    # Above we changed some of the latest tracks to recent add tracks. Now were going to determine
    # what percentage of each of those cats to use. We'll first come up with their percentages as
    # part of the original latest pct. For example, if the original latest pct was 50 and we now
    # have 10 recentadd tracks and 20 latest tracks then the recentadd percentages would be 50 * 10 / (10 +20)
    # Then well add a 20% preference to the recentadd % so these will play more freaquently 
    #          recent add preferecne * (orig latest pct * recentadd track cnt / (recentadd track cnt = latest_track cnt))
    #orig_recentadd_pct = float(c_pct[1]) * track_cnt[0] / (track_cnt[0] + track_cnt[1])
    weightinc_pct=float("1." + weightinc_pct)
    c_pct[0] = round(weightinc_pct * float(c_pct[1]) * track_cnt[0] / (track_cnt[0] + track_cnt[1]))
    c_pct[1] = round(float(c_pct[1]) - float(c_pct[0]))
  else:
    c_pct[0] = 0

  #print("c_pct[] after",c_pct,"orig_recentadd_pct=",orig_recentadd_pct)
  #print("create_recentadd_cat=",create_recentadd_cat," Latest/recent %=",track_cnt[1], track_cnt[0], "gpct[0]=",c_pct[0], "gpct[1]=",c_pct[1])
 
  nbr_of_cat_songs= [round(playlist_tot_songs*float(c_pct[0])/100),
                      round(playlist_tot_songs*float(c_pct[1])/100),
                      round(playlist_tot_songs*float(c_pct[2])/100),
                      round(playlist_tot_songs*float(c_pct[3])/100),
                      round(playlist_tot_songs*float(c_pct[4])/100),
                      round(playlist_tot_songs*float(c_pct[5])/100)]
  
  # The eq list is used to compute the right spacing of cats in the playlist thus insuring it has the 
  # right number of tracks of each cat.
  
  if create_recentadd_cat   == "Yes":
    eq = [100/nbr_of_cat_songs[0],100/nbr_of_cat_songs[1], 100/nbr_of_cat_songs[2], 100/nbr_of_cat_songs[3],100/nbr_of_cat_songs[4],100/nbr_of_cat_songs[5]]
  else:
    eq = [0, 100/nbr_of_cat_songs[1],100/nbr_of_cat_songs[2], 100/nbr_of_cat_songs[3],100/nbr_of_cat_songs[4],100/nbr_of_cat_songs[5]]
  
  tot_eq = [eq[0],eq[1],eq[2],eq[3],eq[4],eq[5]]

 
 
  debug_out(0,["INFO","Plylst Lngth", playlist_length, "minutes."])
  debug_out(0,["INFO","Total Songs", playlist_tot_songs])
  debug_out(0,["INFO","Create recentadd", create_recentadd_cat])
  debug_out(0,["INFO","Recentadd Date", recentadd_date])
  debug_out(0,["INFO","Create Playlist", create_playlist])
  debug_out(0,["INFO","Debug Level", debug_level])
  
  debug_out(0,["INFO", "# # # # # # # # # # # # # # # # # # # # # ","x"])
  debug_out(0,["INFO", "Category","Pct",'PlylstSongs',"Tot Songs"])
  debug_out(0,["INFO", "----------","----",'-----------',"---------"])
  #exit()
  for x in range(len(cats)):
    debug_out(0,["INFO",cats[x],float(c_pct[x]),nbr_of_cat_songs[x],track_cnt[x]])

  
# # # # # # # #
# This funcition lays out the order of tracks based on the correct cat spacing to insure the right nbr
# of tracks for each cat are included. Once we finish writing out this file we'll reopened it for read 
# so we can start finding tracks to match the cat
# # # # # # # #
def  build_proces_db_cat_file():
  #debugpy.breakpoint()
  f1 = open("process_db_cat_fin_order.txt", "w")
  for x in range(0,playlist_tot_songs):

    if create_recentadd_cat == "Yes":
      for x in range(6):
        amt=int(tot_eq[x])
        if amt<=tot_eq[0] and amt<=tot_eq[1] and amt<=tot_eq[2] and amt<=tot_eq[3] and amt<=tot_eq[4] and amt<=tot_eq[5]:
            tot_eq[x]=tot_eq[x] + eq[x]
            debug_out(2,["check_a_row recentadd " , cats[x], tot_eq[x] ])
            break
    else:
      for x in range(5):
        y=x+1
        amt=int(tot_eq[y])
        if amt<=tot_eq[1] and amt<=tot_eq[2] and amt<=tot_eq[3] and amt<=tot_eq[4] and amt<=tot_eq[5]:
            tot_eq[y]=tot_eq[y] + eq[y]
            debug_out(2,["check_a_row no recentadd" , cats[y], tot_eq[y] ])
            x = x + 1
            break
    #return_val=cats[x]
    f1.write(cats[x] + '\n')
  #  f1.write(check_a_row()+'\n')
  f1.close()
  return


# # # # # # #
# Determines if the current artist hasn't been played too recently based on 
# cat artist repeat interval
# # # # # # # 
def check_artist_repeat():
  global artist, artist_last_played,last_played
  last_played_cur.execute('''select g.last_played, cat, a.last_played
                              from artist_last_played  g
                                  ,(select max(last_played) last_played from artist_last_played 
                                    where artist=?) a
                              where artist=?
                                and cat=?'''
                              ,(artist, artist,cat,))
  row=last_played_cur.fetchone()
  debug_out(4,["check_artist_repeat:","artist:",artist,"cat:",cat,cnt,"last_played",last_played,row])
  debug_out(4,["  artist_last_played row(artists last_played|cat|artists cat last_played) =:",row])
  
  if row is None:
    #Really Not sure why the above select would not return a row. The Artist_last_played
    #is loaded in load_sqlite.py based on all tracks so it should be good to go
    debug_out(0,"This shouldn't happen so I'm exiting - gonna have to debug this one")
    exit()
    insert_stmt='''insert into artist_last_played
                (artist, cat, last_played)
                values (?,?,?);''',(artist, cat, cnt)
    sql_stmnt.execute(insert_stmt,(artist,cat,cnt))
    conn.commit
  else:
    artist_cat_last_played = row[0]
    artist_last_played = row[2]
    debug_out(4,[artist," Loop cnt=",cnt," artist_cat_last_played=",artist_cat_last_played,"artist_last_played=",artist_last_played, cat,song, row])
    if artist_last_played == 0 or artist_last_played + cat_repeat < cnt:
      debug_out(5,["Valid track to write to playlist, row =",row])
      line1='#EXTINF: ' + str(length) + ',' + artist + " - " + song 
      f2.write(line1 + "\n")
      f2.write(location + "\n")
      if debug_level>0:
        frmt="{:<10s}{:<42s}{:<32s}{:<12s}"
        f3.write(frmt.format("#" + cat,"#" + artist,"#" + song,"#" + str(length) + "\n"))
        #f3.write(cat + "," + artist + " - " + song + "," + str(length) + "\n")
      artist_last_played=cnt+1
      sql_stmnt.execute('''update artist_last_played 
                                  set last_played = ?
                                where artist = ?
                                  and cat = ?;''',(artist_last_played,artist,cat))
      return_val=True
    else:
      debug_out(5,["!! ",cat," Artist played too requently - should be skipped. Artist_last_played + cat repeat not < track cnt",str(artist_last_played) +"+"+str(cat_repeat)+" not < " + str(cnt) ])
      return_val=False
      
    conn.commit
    return return_val
# END check_artist_repeat function

def open_cat_track_cursors():
  #This is the cursor of all the tracks for the cat we're trying to find a track for. 
  #I call this a cursor (cause it really is) but we'll only ever selects one row for each execution.
  debug_out(4,["open_cat_track_cursors:",cat,cnt])

  cat_cursor.execute('''select song, artist, last_play_dt, last_played, rating, length, repeat_cnt, location 
                          from tracks 
                        where cat = ? 
                          and last_played <= ? 
                          order by last_play_dt''',(cat,cnt,))

# # # # # # # # 
# This function gets a row from the cat cursor that matches the cat from the cat file. The row will be least recently played
# track for that category. If the row meets the artist repeat rules for this cat it will update that record's last_played
# with 999999 to indicate it shouldn't be selected the next time the cursor is built.
# If it doesn't meet the repeat rule it will update last_played for all recs for that artist in this cat with
# artist_last_played plus the repeat interval. This will keep this artist from being included in the cursor until the 
# loop count gets to the artist repeat interval. If it doesn't meet the repeat rules this function will be called again
# until we find a row for this category that meets the artist repeat rules
# # # # # # # # 
def process_cat_track(cnt):
  global artist, length, song, location, last_played, cat_tracks_looped
  debug_out(2,["process_cat_track - " + cat,cnt])
  open_cat_track_cursors()
  # If a cat doesn't have enough songs to match nbr_of_<cat>_songs then when we get to the end we need to reset that
  # cat and start from its beginning.
  try:
    song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=cat_cursor.fetchone()
  except TypeError:
    if cat_tracks_looped == "No":
      debug_out(0,["INFO","Processed all '"+cat+"' tracks. Need to start over.","last_played="+ str(cnt)])
      cat_tracks_looped = "Yes"
      sql_stmnt.execute('update tracks set last_played=0 where cat = ?;',(cat,))
      open_cat_track_cursors()
      song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=cat_cursor.fetchone()
    else:
      debug_out(0,["ERROR","Not enoough '"+cat+"' tracks to build playlist using repeat value of " + str(cat_repeat) + ". last_played="+ str(cnt)])
      debug_out(0,["ERROR","Repeat val for  '"+cat+"' can not be more than " + str(cnt - artist_last_played) + ". last_played="+ str(cnt)])
      
      exit(20)
          
  if check_artist_repeat() == False:
    debug_out(3,["Failed artist repeat - Need to find another "+ cat + "record"])
  
    # We failed the artist repeat so set last_played so this artist won't be included till its time again
    sql_stmnt.execute('''update tracks set last_played=?
                        where artist= ?
                            and cat = ?
                            and last_played <> 999999;
                      ''',(artist_last_played+cat_repeat+1,artist,cat))
    return_val=False
  else:
    debug_out(3,["Passed artist repeat"])
  
    # We found a valid track that can be added to the play list so update it in the tracks table so the song wont 
    # be eligible in the future
    sql_stmnt.execute('''update tracks set last_played=999999
                          where song = ?
                            and artist = ?
                            and cat = ?;
                      ''',(song,artist,cat))
    return_val=True
  
  debug_out(2,[" End - return_val="+str(return_val)])
  conn.commit
  return(return_val) # End process_cat_track function

def main(dbug_lvl=debug_level,
        g_cats=cats,
        pct=c_pct,
        playlist_nm=playlist_name,
        playlist_lgth=playlist_length,
        create_rcntadd_cat=create_recentadd_cat, recentadd_dt=recentadd_date, w_pct=weightinc_pct,
        create_plylist=create_playlist,
        ):  
  #debugpy.breakpoint()
  global  debug_level, create_playlist,playlist_length, recentadd_date, create_recentadd_cat, c_pct, weightinc_pct
  global  cat, f2, f3,cnt, cat_repeat, cat_tracks_looped, df, cats
  if write_debug_to_file == True:
    df = open("debug.log", "w")
  f2=""
  debug_out(0,["Start of module"])
  
  debug_level=dbug_lvl
  playlist_length=playlist_lgth
  recentadd_date=recentadd_dt
  create_recentadd_cat=create_rcntadd_cat
  c_pct=pct
  weightinc_pct=w_pct
  playlist_name=playlist_nm
  create_playlist=create_plylist
  cats=g_cats
  
  debug_out(1,["main function intial parm values"])
  debug_out(1,[" debug_level",debug_level])
  debug_out(1,[" cats",cats])

  initialize_things()
  if create_playlist == 'No':
    conn.commit()
    conn.close()
    df.close() # Debug file
    return(playlist_tot_songs,nbr_of_cat_songs)
  # MAIN LOOP
  # All the functions have been defined, now gonna start doing some work
  # First we'll write theprocess_db_cat_fin_order.txt file with all the categories laid out in the correct sequence. Eash record
  # is a cat place holder for the right song track. Now need to find the last recently played song for that cat and then make 
  # sure the artist doesn't fail the artist_last_played check and if all is good write it out to playlist.m3u
  build_proces_db_cat_file()
    
  # # # # # # # # # # # # # # # # # #
  #  We need to reset the artist_last_played table from any earlier script runs
  # # # # # # # # # # # # # # # # # #

  sql_stmnt.execute('''delete from artist_last_played;''')

  sql_stmnt.execute('''insert into artist_last_played
                            (artist, last_played, cat)
                            select artist, 0, cat
                              from tracks
                          group by artist, cat;''')

  f2 = open(playlist_name+".m3u", "w")
  f2.write("#EXTM3U" + "\n")
  f3 = open("playlist_debug.log", "w")
  

  # Since this is the "real" beginning of the script, need to initialize repeat_cnt and last_played.
  sql_stmnt.execute('update tracks set repeat_cnt = 1, last_played=0;')

  # Now we'll read back in the cat file so we can match each cat record with an appropriat track meeting all rules
  with open(r"process_db_cat_fin_order.txt", 'r') as f1:
   for cnt, line in enumerate(f1):
    cat=line.strip()
    cat_idx=cats.index(cat)
    cat_repeat=repeat[cat_idx]
    cat_tracks_looped="No"
  
    debug_out(1,["Main Loop calling process_cat_track ",cnt, cat])
    while process_cat_track(cnt) == False:
      debug_out(1,[" Failed artist repeat - recalling process_cat_track"])

  debug_out(1,["End of process_db_cat_file_order.txt. cnt=",cnt])

  conn.commit()
  conn.close()

  debug_out(0,["# # # # # # # # # # # # # # # # # # # # # "])
  debug_out(0,["# Script execution complete. Final track count=",cnt+1])
  debug_out(0,["# # # # # # # # # # # # # # # # # # # # # "])

 # f1.close() # process_db_cat_fin_order.txt (with statement automatically closes files when done - I think)
  f2.close() # m3u file
  f3.close() # m3u debug file
  df.close() # Debug file

  return(playlist_tot_songs,nbr_of_cat_songs)
  
  # End of "main" function

if __name__ == "__main__":
  definable_cats=["Latest","In Rot","Other","Old","Damaged"]
  cats = recentadd_cat + definable_cats
  main(dbug_lvl=5,
        g_cats=cats,pct=c_pct,
        playlist_nm=playlist_name,playlist_lgth=playlist_length,
        create_rcntadd_cat="Yes", recentadd_dt=recentadd_date, w_pct=str(20),
        create_plylist="Yes")  