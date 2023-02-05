from lib2to3.pgen2.pgen import DFAState
from operator import truediv
from re import X
from telnetlib import theNULL
import xml.etree.ElementTree as ET
import sqlite3
import array
import traceback
import sys
from datetime import datetime,timedelta
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askyesno


spc = {}
spc[0] = ""
spc[1] = ""
spc[2] = " "
spc[3] = "  "
spc[4] = "   "
spc[5] = "    "

cnt=0
cat=""
create_recentadd_cat=False
today_dt=datetime.now().strftime("%Y-%m-%d")
date_added=datetime.now() - timedelta(days=180)
playlist_name="playlist"
create_playlist="Yes"

# Here we define the categories were using and then start
# defining values to associate with them.
categories=["RecentAdd","Latest","In Rot","Other","Old","Album"]
repeat = [15,20,30,50,50,50]
tot_c_trk_cnt=[0,0,0,0,0,0]
c_trk_cnter=[0,0,0,0,0,0]

# Set some default values
cat_pct=[str(0),str(50),str(20),str(10),str(10),str(10)]
cat_rpt=[str(15),str(20),str(30),str(50),str(50),str(50)]
playlist_length=1000
debug_level=0
write_debug_to_file = True
weighting_pct=str(20)

def debug_out(debug_val,debug_line,frmt="z"):
#    print("debug val=",debug_val,"debug line",debug_line)
    if debug_val <= debug_level:
      #Gi=0
      tupl = (debug_line)
      strg = spc[debug_val]
      x = strg + tupl[0]
      tupl[0] = str(x)
      tupl_nbr_of_vals= len(tupl)
      if tupl_nbr_of_vals <= 11:
        for i in range(tupl_nbr_of_vals, 12):
          tupl=tupl + ["",]
      else:
         tupl[0] = "DEBUG ERROR" 
         tupl[1] = "Too many debug items to display"
         tupl[2] = debug_line
      if frmt == "f":
        ltrl=tupl[0]
        strg=ltrl.format(str(tupl[1]),str(tupl[2]),str(tupl[3]),str(tupl[4]),str(tupl[5]),str(tupl[6]),str(tupl[7]),str(tupl[8]))
      else:
        frmt="{:<20s}{:<12s}{:<12s}{:<12s}{:<12s}{:<12s}{:<12s}{:<12s}{:<12s}"
        strg=frmt.format(tupl[0],str(tupl[1]),str(tupl[2]),str(tupl[3]),str(tupl[4]),str(tupl[5]),str(tupl[6]),str(tupl[7]),str(tupl[8]))
      if __name__ == "__main__":
        print(strg)
      if write_debug_to_file == True:
        df.write(strg + "\n")
        
def main(dbug_lvl=debug_level,
        c_pct=cat_pct,
        c_rpt=cat_rpt,
        playlist_nm=playlist_name,
        playlist_lgth=playlist_length,
        create_rcntadd_cat=create_recentadd_cat, recentadd_dt=date_added, weighting_pct=weighting_pct,
        create_plylist=create_playlist,
        ):  
  global df, debug_level, create_playlist
  debug_level=dbug_lvl
  create_playlist=create_plylist
  if write_debug_to_file == True:
    df = open("debug.log", "w")

  playlist_tot_songs=int(int(playlist_lgth)/4) # avg song is 4 minutes
  
  # Connect to db
  conn = sqlite3.connect('kTunes.sqlite')
  sql_stmnt = conn.cursor()
  
  debug_out(1,["Resetting RecentAdd to Latest:",recentadd_dt])
  # If the RecentAdd switch had been set in an earlier run, need to switch back with this update
  sql_stmnt.execute('''update tracks set category = 'Latest'
                         where category = 'RecentAdd' COLLATE NOCASE''')

  if create_rcntadd_cat is True:
    debug_out(1,["create_recently_added_cat:",recentadd_dt])
    sql_stmnt.execute('''update tracks set category = 'RecentAdd'
                         where category = 'Latest' COLLATE NOCASE
                           and date_added >= ?''',(recentadd_dt,))
  
  for x in range(len(categories)):
    sql_stmnt.execute('''select count(*) from tracks
                           where category=?''',(categories[x],))
    row=sql_stmnt.fetchone()
    tot_c_trk_cnt[x]=row[0]
  if create_rcntadd_cat is True:
    print("c_pct[] before",c_pct)
    # Above we changed some of the latest tracks to recent add tracks. Now were going to determine
    # what percentage of each of those categories to use. We'll first come up with their percentages as
    # part of the original latest pct. For example, if the original latest pct was 50 and we now
    # have 10 recentadd tracks and 20 latest tracks then the recentadd percentages would be 50 * 10 / (10 +20)
    # Then well add a 20% preference to the recentadd % so these will play more freaquently 
    #          recent add preferecne * (orig latest pct * recentadd track cnt / (recentadd track cnt = latest_track cnt))
    #orig_recentadd_pct = float(c_pct[1]) * tot_c_trk_cnt[0] / (tot_c_trk_cnt[0] + tot_c_trk_cnt[1])
    weighting_pct=float("1." + weighting_pct)
    c_pct[0] = round(weighting_pct * float(c_pct[1]) * tot_c_trk_cnt[0] / (tot_c_trk_cnt[0] + tot_c_trk_cnt[1]))
    c_pct[1] = round(float(c_pct[1]) - float(c_pct[0]))
  else:
    c_pct[0] = 0

  nbr_of_cat_songs= [round(playlist_tot_songs*float(c_pct[0])/100),
                     round(playlist_tot_songs*float(c_pct[1])/100),
                     round(playlist_tot_songs*float(c_pct[2])/100),
                     round(playlist_tot_songs*float(c_pct[3])/100),
                     round(playlist_tot_songs*float(c_pct[4])/100),
                     round(playlist_tot_songs*float(c_pct[5])/100)]
  
  # The cat_inv_pct is the percentage of the inverse of the number of songs a cat should have in a playlist.
  # For example: We only want are playlist to containe 20 of the first cat. So cat_inv_pct = 100 * 1/20
  # This is used to compute the right spacing of categories in the playlist based on number of tracks per cat.
  # We'll keep a sum of the cat_inv_pct for each cat as we build out the playlist. By the time we get end of the playlist
  # the sum for each cat should all be the same and they should match the total playlist count
  if create_rcntadd_cat is True:
    cat_inv_pct = [100/nbr_of_cat_songs[0],100/nbr_of_cat_songs[1], 100/nbr_of_cat_songs[2], 100/nbr_of_cat_songs[3],100/nbr_of_cat_songs[4],100/nbr_of_cat_songs[5]]
  else:
    cat_inv_pct = [0, 100/nbr_of_cat_songs[1],100/nbr_of_cat_songs[2], 100/nbr_of_cat_songs[3],100/nbr_of_cat_songs[4],100/nbr_of_cat_songs[5]]
  tot_cat_inv_pct = [cat_inv_pct[0],cat_inv_pct[1],cat_inv_pct[2],cat_inv_pct[3],cat_inv_pct[4],cat_inv_pct[5]]

  playlist_name=playlist_nm
 
  debug_out(0,["INFO","Plylst Lngth", playlist_lgth, "minutes."])
  debug_out(0,["INFO","Total Songs", playlist_tot_songs])
  debug_out(0,["INFO","Create recentadd", create_rcntadd_cat])
  debug_out(0,["INFO","Recentadd Date", recentadd_dt])
  debug_out(0,["INFO","Create Playlist", create_playlist])
  debug_out(0,["INFO","Debug Level", debug_level])
  debug_out(0,["INFO", "# # # # # # # # # # # # # # # # # # # # # ","x"])
  debug_out(0,["INFO", "Genre","Pct",'PlylstSongs',"Tot Songs"])
  debug_out(0,["INFO", "----------","----",'-----------',"---------"])
  for x in range(len(categories)):
    debug_out(0,["INFO",categories[x],float(c_pct[x]),nbr_of_cat_songs[x],tot_c_trk_cnt[x]])

  if create_playlist == 'No':
    conn.commit()
    conn.close()
    df.close() # Debug file
    return(playlist_tot_songs,nbr_of_cat_songs,False)
  else:
    # check if playlist already exists
    sql_stmnt.execute('''select "x" from playlist where playlist_nm = ?;''',(playlist_name,))
    if sql_stmnt.fetchone():
      # create the root window
      root = tk.Tk()
      #root.title('Tkinter Yes/No Dialog')
      #root.geometry('300x150')
      root.withdraw()  # hide main window
      answer = askyesno(title=None, message="This playlist already exist do you want to overwrite it?")
      if answer:
        root.destroy()
      else:
        root.destroy()
        return(playlist_tot_songs,nbr_of_cat_songs,True)

    tot_c_trk_cnt[x]=row[0]
    
    for x in range(len(categories)):
      insert_stmt='''insert or replace into playlist
                     (playlist_dt,playlist_nm,length,nbr_of_songs,recentadd_dt,debug_level,category,pct,nbr_of_cat_playlist_songs,nbr_of_cat_songs)
                     values (?,?,?,?,?,?,?,?,?,?);'''
      sql_stmnt.execute(insert_stmt,(today_dt,playlist_name,playlist_lgth, playlist_tot_songs, recentadd_dt, debug_level, categories[x], float(c_pct[x]),nbr_of_cat_songs[x],tot_c_trk_cnt[x],))
  
  def get_cursor_rec(cat):
    global artist, length, play_cnt, song, date_song_added, location, played_sw, cat_cnt, artist_cat_cnt, last_play_dt, csr_row_cnt

    # This is the cursor of all the tracks for the cat we're trying to find a track for. 
    # We're only going to pull the first row each time we open this cursor but oh well.
    debug_out(4,["opening cat_track cursor. Cat:{}, cnt:{}, cat_trk_cnt:{}",cat, cnt,c_trk_cnter[cat_idx]],"f")
    where_stmnt = '''
        where (   category = '{}'
               or (   '{}' = 'RecentAdd'
                   and category = 'Latest'
                   and recent_add_subcat is TRUE)
                   )
           and (   artist_cat_cnt + {} <= cat_cnt 
                )
           and played_sw = FALSE
        order by last_play_dt;'''.format(cat, cat, cat_repeat,)
    sql = '''select song, artist, last_play_dt, played_sw, cat_cnt, artist_cat_cnt, rating, length, play_cnt, date_added, location
             from tracks ''' + where_stmnt
    
    sql2 = '''select count(*) cursor_cnt
                            from tracks ''' + where_stmnt

    cat_cur.execute(sql)
     
    # If a cat doesn't have enough songs to match nbr_of_<cat>_songs then when we get to the end we need to reset that
    # cat and start from its beginning.
    try:
      song,artist, last_play_dt, played_sw, cat_cnt, artist_cat_cnt, rating, length, play_cnt, date_song_added, location=cat_cur.fetchone()
    except TypeError:
      # There were no records returned from the cursor so we need to reset there records so we can start over again
      debug_out(0,["INFO - Processed all {} tracks. Need to start over. Cnt:{}. g_grk_cnt", cat, cnt, c_trk_cnter[cat_idx]],"f")
      if debug_level>0:
        f3.write("Reseting {} cursor after {} {} tracks".format(cat,c_trk_cnter[cat_idx],cat) + "\n")

      sql_stmnt.execute('update tracks set played_sw = FALSE  where category = ?;',(cat,))
      conn.commit
      # Reopening cursor after reset
      cat_cur.execute(sql)
      try:
        song,artist, last_play_dt, played_sw, cat_cnt, artist_cat_cnt, rating, length, play_cnt, date_song_added, location=cat_cur.fetchone()
      except:
        debug_out(5,["Cursor did not return any rows after reset. SQL statement was", sql])
   
    cat_cur.execute(sql2)
    csr_row_cnt=cat_cur.fetchone()
    debug_out(5,["Cursor returned {} rows. artist:{}, song:{}, played_sw:{}, artist_cat_cnt:{}, cat_cnt:{}", str(csr_row_cnt),artist,song,played_sw,artist_cat_cnt,cat_cnt],"f")

  def process_cat_track(cnt):
    global artist_cat_cnt, cat_cnt
    return_val=False
    debug_out(2,["process_cat_track"])
    get_cursor_rec(cat)
    debug_out(3,["process_cat_track - writing to playlist. Genre:{}, cat_cnt:{}, cat_repeat:{}, cat_idx:{}",cat,c_trk_cnter[cat_idx],cat_repeat,cat_idx],"f")
    line1='#EXTINF: ' + str(length) + ',' + artist + " - " + song 
    f2.write(line1 + "\n")
    f2.write(location + "\n")
    #Don't wannan here this song again until we get through all other songs in the category so set played_sw to TRUE
    sql_stmnt.execute('''update tracks
                            set played_sw = TRUE
                              where artist = ?
                                and song = ?;''',(artist,song,))
    
    # Were setting the artist_cat_cnt for all recs of this artest/category to the current value of the count 
    # total # of recs from this category. This way we wont include any recs from this artist in this cat
    # until category count is <repeat cnt> higher than the artist_cat_cnt
    # till its their time
    #cat_cnt += 1
    if cat in ['Latest', 'RecentAdd']:
      cat_val= '("Latest", "RecentAdd")'
    else:
      cat_val= '("' + cat + '")'
    stmnt='''update tracks set cat_cnt = cat_cnt + 1 where category in ''' + cat_val
    sql_stmnt.execute(stmnt)

    stmnt='''update tracks set artist_cat_cnt = cat_cnt where artist = ? '''#and category in '''+ cat_val
    sql_stmnt.execute(stmnt,(artist,))
    
    stmnt='''insert or replace into playlist_tracks
                    (playlist_dt,playlist_nm,track_cnt,artist,song,category,length,play_cnt,last_play_dt,cat_cnt,artist_cat_cnt)
                    values (?,?,?,?,?,?,?,?,?,?,?);''' 
    sql_stmnt.execute(stmnt,(today_dt,playlist_name,cnt,artist,song,cat,length/1000/60,play_cnt, last_play_dt,cat_cnt,artist_cat_cnt,))
    
    if debug_level>0:
      sng_lngth = str(round(length/1000/60,2))
      frmt="{:<20s}{:<20s} L-{:5s} C:{:11s} R:{:<3d} cnt:{:<3d} c-cnt:{:<3d} ac-cnt:{:<3d} csr-cnt:{:<4s} lp-dt:{:<13s} {:<9s} {:<10s}"
      f3.write(frmt.format(artist[0:20], song[0:20], str(round(length/1000/60,2)), 
      cat, cat_repeat,cnt, cat_cnt,artist_cat_cnt,str(csr_row_cnt[0]),str(last_play_dt)[0:12],
      str(play_cnt),date_song_added) + "\n")
                            
    debug_out(2,[" End - return_val="+str(return_val)])
    conn.commit
    return(return_val)

  # MAIN PROCESSING STARTS HERE
  cat_cur = conn.cursor()
  f2 = open(playlist_name+".m3u", "w")
  f2.write("#EXTM3U" + "\n")
  if debug_level>0:
    f3 = open("playlist_debug.log", "w")
    
  # Need to set last_play_dt to 0 if its a brand new track
  sql_stmnt.execute('update tracks set last_play_dt = 0 where last_play_dt = "Unknown";')

  # Make sure all tracks are eligble
  for x in range(len(categories)):
    sql_stmnt.execute('''update tracks set played_sw=FALSE, artist_cat_cnt = 0, cat_cnt = ?
                         where category = ?;''',(cat_rpt[x],categories[x]))
  
  # Everythings set to go. Lets start creating the playlist
  for cnt in range(0,playlist_tot_songs):
    if create_rcntadd_cat is True:
      for x in range(6):
        amt=int(tot_cat_inv_pct[x])
        if amt<=tot_cat_inv_pct[0] and amt<=tot_cat_inv_pct[1] and amt<=tot_cat_inv_pct[2] and amt<=tot_cat_inv_pct[3] and amt<=tot_cat_inv_pct[4] and amt<=tot_cat_inv_pct[5]:
            tot_cat_inv_pct[x]=tot_cat_inv_pct[x] + cat_inv_pct[x]
            debug_out(2,["check_a_row recentadd " , categories[x], tot_cat_inv_pct[x] ])
            break
    else:
      for x in range(5):
        y=x+1
        amt=int(tot_cat_inv_pct[y])
        if amt<=tot_cat_inv_pct[1] and amt<=tot_cat_inv_pct[2] and amt<=tot_cat_inv_pct[3] and amt<=tot_cat_inv_pct[4] and amt<=tot_cat_inv_pct[5]:
            tot_cat_inv_pct[y]=tot_cat_inv_pct[y] + cat_inv_pct[y]
            debug_out(2,["check_a_row no recentadd" , categories[y], tot_cat_inv_pct[y] ])
            x = x + 1
            break
    cat=categories[x]
    debug_out(1,["get a cat:",categories[x]])
    cat_idx=categories.index(cat)
    cat_repeat=cat_rpt[cat_idx]
    debug_out(1,["Main Loop:",cnt, cat])
    while process_cat_track(cnt) == True:
      debug_out(1,[" End - Main Loop","hello"])


  debug_out(1,["End of process_db_cat_file_order.txt. cnt=",cnt])

  conn.commit()
  conn.close()

  debug_out(0,["# # # # # # # # # # # # # # # # # # # # # "])
  debug_out(0,["# Script execution complete. Final track count=",cnt+1])
  debug_out(0,["# # # # # # # # # # # # # # # # # # # # # "])

  f2.close() # m3u file
  if debug_level>0:
    f3.close() # m3u debug file
  df.close() # Debug file

  return(playlist_tot_songs,nbr_of_cat_songs,False)
  
  # End of "main" function

if __name__ == "__main__":
   main(dbug_lvl=5,c_pct=cat_pct,playlist_nm=playlist_name,playlist_lgth=playlist_length,create_rcntadd_cat=True,
        recentadd_dt=date_added,
        weighting_pct=str(20),
        create_plylist="Yes")  
  
   
