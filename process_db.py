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
from operator import itemgetter 
import numpy as np


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
    global cat
    
    if debug_val <= debug_level:
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
      else:
        df.write(strg + "\n")
        
def main(config): 
  # Accepts a configuration dictionary as input.
  # Sets up the database connection.
  # Updates the database to ensure that all tracks are eligible for playlist selection.
  # Iterates through the desired number of tracks for the playlist.
  # For each track, it selects a track from a specific category, ensuring that the same artist or category is not repeated too quickly.
  # Updates track and category counters to control repeat intervals.
  # Records track information in the playlist.
  global df, debug_level, create_playlist, repeat, last_song
  last_song = " "
  misc, category = itemgetter('misc','categories')(config)
  debug_level=int(misc['debug_lvl'])
  if __name__ != "__main__":
    df = open('debug.log', 'w')
  debug_out(1,["Main - Passed Dictionary:",config])
  playlist_name = misc['playlist_name']
  playlist_lgth = misc['playlist_lgth']
  create_playlist = misc['create_playlist']
  create_rcntadd_cat = misc['recently_added_switch']
  recentadd_play_cnt = misc['ra_play_cnt']
  weighting_pct = misc['ra_weighting_factor']

  categories = ["RecentAdd"]
  c_pct = [0]
  repeat = [15]
  

  category_dict=category
  
  # Loop through the dictionary and insert values to arrays
  for i, (key, value) in enumerate(category_dict.items()):
    if key.startswith("cat") and not key.endswith("_pct") and not key.endswith("_repeat"):
        categories.insert(i+1, value) 
    elif key.endswith("_pct"):
        c_pct.insert(i//3+1, value) 
    elif key.endswith("_repeat"):
        repeat.insert(i//3+1, value)
  
    playlist_tot_songs=int(int(playlist_lgth)/4) # avg song is 4 minutes
  
  # Connect to db
  conn = sqlite3.connect('kTunes.sqlite')
  sql_stmnt = conn.cursor()
  
  debug_out(1,["Resetting RecentAdd to Latest:"])
  # If the RecentAdd switch had been set in an earlier run, need to switch back with this update
  sql_stmnt.execute('''update tracks set category = 'Latest'
                         where category = 'RecentAdd' COLLATE NOCASE''')

  if create_rcntadd_cat == 'on':
    debug_out(1,["create_recently_added_cat with play_cnt:",recentadd_play_cnt])
    sql_stmnt.execute('''update tracks set category = 'RecentAdd'
                         where category = 'Latest' COLLATE NOCASE
                           and play_cnt <= ?''',(recentadd_play_cnt,))
  
  for x in range(len(categories)):
    sql_stmnt.execute('''select count(*) from tracks
                           where category=?''',(categories[x],))
    row=sql_stmnt.fetchone()
    tot_c_trk_cnt[x]=row[0]
  if create_rcntadd_cat == 'on':
    print("c_pct[] before",c_pct)
    # Above we changed some of the latest tracks to recent add tracks. Now were going to determine
    # what percentage of each of those categories to use. We'll first come up with their percentages as
    # part of the original latest pct. For example, if the original latest pct was 50 and we now
    # have 10 recentadd tracks and 20 latest tracks then the recentadd percentages would be 50 * 10 / (10 +20)
    # Then well add a 20% preference to the recentadd % so these will play more freaquently 
    #          recent add preferecne * (orig latest pct * recentadd track cnt / (recentadd track cnt = latest_track cnt))
    #orig_recentadd_pct = float(c_pct[1]) * tot_c_trk_cnt[0] / (tot_c_trk_cnt[0] + tot_c_trk_cnt[1])
    weighting_pct=float("1." + weighting_pct)
    print(weighting_pct, float(c_pct[1]), tot_c_trk_cnt[0] ,  tot_c_trk_cnt[1])
    c_pct[0] = round(weighting_pct * float(c_pct[1]) * tot_c_trk_cnt[0] / (tot_c_trk_cnt[0] + tot_c_trk_cnt[1]))
    c_pct[1] = round(float(c_pct[1]) - float(c_pct[0]))
    print("c_pct[] after",c_pct)
  else:
    c_pct[0] = 0

  nbr_of_cat_songs= [round(playlist_tot_songs*float(c_pct[0])/100),
                     round(playlist_tot_songs*float(c_pct[1])/100),
                     round(playlist_tot_songs*float(c_pct[2])/100),
                     round(playlist_tot_songs*float(c_pct[3])/100),
                     round(playlist_tot_songs*float(c_pct[4])/100),
                     round(playlist_tot_songs*float(c_pct[5])/100)]
  
  # The cat_inv_pct is the percentage of the inverse of the number of songs a cat should have in a playlist.
  # For example: Say We only want are playlist to contains 125 song of the first cat. It's cat_inv_pct is = 100 * 1/125 = .8
  # This is used to compute the right spacing of categories in the playlist based on number of tracks per cat.
  # We set tot_cat_inv_pct to the values we just calculated. Later, when we're building the playlist, 
  # we'll use this to sum of the cat_inv_pct for each cat as we build out the playlist.
  # And by the time we get end of the playlist the sum for each cat should all be the same and they should match the total playlist count
  if create_rcntadd_cat == 'on':
    print(nbr_of_cat_songs[0],nbr_of_cat_songs[1], nbr_of_cat_songs[2], nbr_of_cat_songs[3],nbr_of_cat_songs[4],nbr_of_cat_songs[5])
    cat_inv_pct = [100/nbr_of_cat_songs[0],100/nbr_of_cat_songs[1], 100/nbr_of_cat_songs[2], 100/nbr_of_cat_songs[3],100/nbr_of_cat_songs[4],100/nbr_of_cat_songs[5]]
  else:
    cat_inv_pct = [0, 100/nbr_of_cat_songs[1],100/nbr_of_cat_songs[2], 100/nbr_of_cat_songs[3],100/nbr_of_cat_songs[4],100/nbr_of_cat_songs[5]]
  tot_cat_inv_pct = [cat_inv_pct[0],cat_inv_pct[1],cat_inv_pct[2],cat_inv_pct[3],cat_inv_pct[4],cat_inv_pct[5]]

  #playlist_name=playlist_nm
 
  debug_out(0,["INFO","Plylst Lngth", playlist_lgth, "minutes."])
  debug_out(0,["INFO","Total Songs", playlist_tot_songs])
  debug_out(0,["INFO","Create recentadd", create_rcntadd_cat])
  debug_out(0,["INFO","Recentadd Date", recentadd_play_cnt])
  debug_out(0,["INFO","Create Playlist", create_playlist])
  debug_out(0,["INFO","Debug Level", debug_level])
  debug_out(0,["INFO", "# # # # # # # # # # # # # # # # # # # # # ","x"])
  debug_out(0,["INFO", "Genre","Pct",'PlylstSongs',"Tot Songs", "cat_inv_pct"])
  debug_out(0,["INFO", "----------","----",'-----------',"---------"])
  for x in range(len(categories)):
    debug_out(0,["INFO",categories[x],float(c_pct[x]),nbr_of_cat_songs[x],tot_c_trk_cnt[x],float(cat_inv_pct[x])])

  if create_playlist == 'off':
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
                     (playlist_dt,playlist_nm,length,nbr_of_songs,recentadd_play_cnt,debug_level,category,pct,nbr_of_cat_playlist_songs,nbr_of_cat_songs)
                     values (?,?,?,?,?,?,?,?,?,?);'''
      sql_stmnt.execute(insert_stmt,(today_dt,playlist_name,playlist_lgth, playlist_tot_songs, recentadd_play_cnt, debug_level, categories[x], float(c_pct[x]),nbr_of_cat_songs[x],tot_c_trk_cnt[x],))
  
  def get_cursor_rec(cat):
  
    # This function retrieves a cursor of tracks for a given category.
    
    # Input:
    # - cat: The category for which we want to retrieve the cursor.
    
    # Global Variables:
    # - artist, length, play_cnt, song, date_song_added, location, played_sw
    # - cat_cnt, artist_cat_cnt, last_play_dt, csr_row_cnt
    
    # Function Steps:
    
    # 1. Construct a SQL query to retrieve tracks of the given category that haven't been played yet.
    #    The query also orders the results by the last time each track was played.
    
    # 2. Execute the SQL query using a cursor object.
    
    # 3. Fetch the first row of results from the cursor.
    
    # 4. If there are no results returned by the query (i.e., all tracks in this category have already been played),
    #    then reset all records in this category to mark them as unplayed so they can be played again.
    
    # 5. Return the fetched row of track information or None if there are no unplayed tracks in this category.
    
    # Example Usage:
    # cat_cursor = get_cursor_rec("RecentAdd")
    # track_info = cat_cursor.fetchone()
    # if track_info is not None:
    #     # Process the track information
    # else:
    #     # All tracks in this category have been played, take appropriate action.

    global artist, length, play_cnt, song, date_song_added, location, played_sw, cat_cnt, artist_cat_cnt, last_play_dt, csr_row_cnt

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
        order by last_play_dt;'''.format(cat, cat, cat_repeat_interval,)
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
      # There were no records returned from the cursor so we need to resetting the played_sw so all recs will be eligible again.
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
    if str(csr_row_cnt) == '(509,)':
      debug_out(5,["Cursor returned magic with where_stmnt {}", where_stmnt],"f")
    debug_out(5,["Cursor returned {} rows. ", str(csr_row_cnt),where_stmnt],"f")

    #debug_out(5,["Cursor returned {} rows. artist:{}, song:{}, played_sw:{}, artist_cat_cnt:{}, cat_cnt:{}, category:{}", str(csr_row_cnt),artist,song,played_sw,artist_cat_cnt,cat_cnt, cat],"f")

  def process_cat_track(cnt):
    # The process_cat_track function is used to get a single track for a given category. 
    # The function first calls the get_cursor_rec function to retrieve a cursor of all the tracks for the given category. 
    # It then writes the current track to the playlist file and updates the database to mark this track as played.
    # The function also updates the cat_cnt and artist_cat_cnt fields in the database for this track’s category and artist. 
    # These fields are used to ensure that each category and artist is played fairly and that no two tracks from the same
    # artist and category are played more frequently than the repeat count.
    global artist_cat_cnt, cat_cnt, last_song
    return_val=False
    debug_out(2,["process_cat_track"])

    get_cursor_rec(cat)
         
    debug_out(3,["process_cat_track - writing to playlist. Genre:{}, cat_cnt:{}, cat_repeat_interval:{}, cat_idx:{}",cat,c_trk_cnter[cat_idx],cat_repeat_interval,cat_idx],"f")
    line1='#EXTINF: ' + str(length) + ',' + artist + " - " + song 
    f2.write(line1 + "\n")
    f2.write(location + "\n")
    #Don't wannan here this song again until we get through all other songs in the category so set played_sw to TRUE
    sql_stmnt.execute('''update tracks
                            set played_sw = TRUE
                              where artist = ?
                                and song = ?;''',(artist,song,))
    
    # Were setting the artist_cat_cnt for all recs of this artist/category to the current value of the count 
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

    # 6/22/23 - I had a bug where I was running out of album tracks in a playlist. It appears it was because in the following statement I'd
    # commented out the 'and category in''' + cat_val' part. This meant everytime an artist was selected it said could not play another album
    # track from that artist till we played at least 50 other album tracks. But we never got to 50 album tracks. They had all been marked to not play
    # till 50 tracks by the 44th album track. So I'm uncommenting the 'catatory' check. I don't recall why I initially commented out.
    # I should have documented it. I'm sure there was a reason. If I come across that reason again and want to comment out this again
    # I could try resetting artist_cat_cnt if/when I run out of tracks. This wouldn't be great because it would cause duplicates of some
    # album tracks in a singel playlist but if you can't come up woth something else...
    stmnt='''update tracks set artist_cat_cnt = cat_cnt where artist = ? and category in '''+ cat_val
    sql_stmnt.execute(stmnt,(artist,))
    
    stmnt='''insert or replace into playlist_tracks
                    (playlist_dt,playlist_nm,track_cnt,artist,song,category,length,play_cnt,last_play_dt,cat_cnt,artist_cat_cnt)
                    values (?,?,?,?,?,?,?,?,?,?,?);''' 
    sql_stmnt.execute(stmnt,(today_dt,playlist_name,cnt,artist,song,cat,length/1000/60,play_cnt, last_play_dt,cat_cnt,artist_cat_cnt,))
    
    if debug_level>9:
      print("artist",artist, " song",song,  "length",length, "cat_repeat_interval", cat_repeat_interval,"cnt",cnt,"cat_cnt",cat_cnt)
      sng_lngth = str(round(length/1000/60,2))
      frmt="{:<20s}{:<20s} L-{:5s} C:{:11s} R:{:<3d} cnt:{:<3d} c-cnt:{:<3d} ac-cnt:{:<3d} csr-cnt:{:<4s} lp-dt:{:<13s} {:<9s} {:<10s}"
      f3.write(frmt.format(artist[0:20], song[0:20], str(round(length/1000/60,2)), cat, cat_repeat_interval,cnt, cat_cnt,artist_cat_cnt,str(csr_row_cnt[0]),str(last_play_dt)[0:12], str(play_cnt),date_song_added) + "\n")
                            
    debug_out(2,[" End - return_val="+str(return_val)])
    conn.commit
    return(return_val)
  
  def song_distribution(c_pct, playlist_tot_songs):
      print("Inside song_distribution c_pct=",c_pct, "Tog songs=",playlist_tot_songs)
      global song_distribution_list
    
      # Calculate the number of items for each category based on percentages
      category_counts = [int((int(percentage) / 100) * playlist_tot_songs) for percentage in c_pct]

      # Calculate initial fractions for each category
#      fractions = [1 / count for count in category_counts]
      fractions = [1 / count if count != 0 else 0 for count in category_counts]


      # Initialize an empty list to store the resulting distribution and a debug list
      song_distribution_list = []
      category_distribution_cnts = []

      # Create a loop to distribute items evenly
      while len(song_distribution_list) < playlist_tot_songs:
          # Find the index of the category with the lowest fraction
          min_fraction_index = np.argmin(fractions)
          
          if create_rcntadd_cat != 'on' and min_fraction_index == 0:
             # If excluding the first category, move to the next category
             min_fraction_index = np.argmin(fractions[1:]) + 1
             # If all categories have been exhausted, exit the loop
             if min_fraction_index is None:
                break
             print("cat 0, ",len(song_distribution_list))
                        
          current_count = len([entry for entry in song_distribution_list if categories[min_fraction_index] in entry])
          
          # Calculate the total count for the selected category
          category_count = category_counts[min_fraction_index]
          
          # Update the fraction for the selected category
          fractions[min_fraction_index] += 1 / category_count
          
          # Add the entry to the result list
          print(f"{categories[min_fraction_index]} {current_count + 1} of {category_count}")
          song_distribution_list.append(f"{categories[min_fraction_index]}")
          category_distribution_cnts.append(f" {current_count + 1} of {category_count}")

      ## Print the final distribution
      for x in range(len(song_distribution_list)):
#      for entry in song_distribution_list:
          print(song_distribution_list[x], category_distribution_cnts[x], x)
      
      return(song_distribution_list)

  # MAIN PROCESSING STARTS HERE

  cat_cur = conn.cursor()
  f2 = open(playlist_name+".m3u", "w")
  f2.write("#EXTM3U" + "\n")
  if debug_level>0:
    f3 = open("playlist_debug.log", "w")
    
  # Need to set last_play_dt to 0 if its a brand new track
  sql_stmnt.execute('update tracks set last_play_dt = 0 where last_play_dt = "Unknown";')

  song_distribution(c_pct, playlist_tot_songs)
  print("after song_distribution")

  # Make sure all tracks are eligble
  for x in range(len(categories)):
    sql_stmnt.execute('''update tracks set played_sw=FALSE, artist_cat_cnt = 0, cat_cnt = ?
                         where category = ?;''',(cat_rpt[x],categories[x]))
  
  # Everythings set to go. Lets start creating the playlist
  # The logic in this for loop will seperate the tracks by category to insure they are spaced evenly based on the percentage the user said they want
  # for each category.
  # tot_cat_inv_pct was initially calculated by divding 100 by the calculated number of song for a category.
  for cnt in range(0,playlist_tot_songs):
    cat=song_distribution_list[cnt]
    cat_idx=categories.index(cat)
    cat_repeat_interval=cat_rpt[cat_idx]
    debug_out(1,["Main Loop:",cnt, cat,cat_idx, cat_repeat_interval])
    while process_cat_track(cnt) == True:
      debug_out(1,[" End - Main Loop","hello"])


  debug_out(1,["End of process_db main cnt=",cnt])

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
def main2(config):  
  misc, categories = itemgetter('misc','categories')(config)
  playlist_name = misc['playlist_name']

  print("playlist name from dict=",playlist_name)
#print(categories)
  return(5,3,False)

if __name__ == "__main__":
   main(dbug_lvl=5,c_pct=cat_pct,playlist_nm=playlist_name,playlist_lgth=playlist_length,create_rcntadd_cat='on',
        recentadd_dt=date_added,
        weighting_pct=str(20),
        create_plylist="Yes")  
  
   
