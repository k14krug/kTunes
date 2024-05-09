from lib2to3.pgen2.pgen import DFAState
from operator import truediv
from re import X
from telnetlib import theNULL
import xml.etree.ElementTree as ET
import logging
import inspect
import sqlite3
import array
import traceback
import sys
from datetime import datetime,timedelta
import tkinter as tk
from tkinter import ttk, Toplevel
from tkinter.messagebox import askyesno
from operator import itemgetter 
import numpy as np

# Key variables in the tracks table:  
#   cat_cnt - The current track count for a given category. All tracks in a category will have the same value for this field.
#   artist_cat_cnt - The value that cat_cnt was when we last selected an artist in this category. 
#                    All tracks for an artist in a category will have the same value for this field.
#   cat_repeat_interval - A constant - The number of tracks that must be played between tracks from an artist in a category.
#     As we search for songs to add we'll only select sounds where the artist_cat_cnt + cat_repeat_interval <= cat_cnt
#     This will ensure that an artist is not played more frequently than the cat_repeat_interval.


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
#date_added=datetime.now() - timedelta(days=180)
playlist_name="playlist"
create_playlist="Yes"

tot_c_trk_cnt=[0,0,0,0,0,0]
c_trk_cnter=[0,0,0,0,0,0]

# Set some default values
cat_pct=[str(0),str(50),str(20),str(10),str(10),str(10)]
#cat_rpt_list=[str(15),str(20),str(30),str(50),str(50),str(50)]
playlist_length=1000
debug_level=0
write_debug_to_file = True
logging.basicConfig(filename='debug.log', filemode='w', level=logging.DEBUG, format='%(message)s')
starting_stack_depth = 0

class CustomDialog(Toplevel):
    def __init__(self, parent, title=None, message=None):
        tk.Toplevel.__init__(self, parent)
        self.title(title)
        self.message = message
        self.result = None
        tk.Label(self, text=self.message).pack()
        tk.Button(self, text="Yes", command=lambda: self.close_dialog(True)).pack()
        tk.Button(self, text="No", command=lambda: self.close_dialog(False)).pack()

        # Position the window
        screen_width = self.winfo_screenwidth() // 2  # half of the total width
        screen_height = self.winfo_screenheight()  # height of the screen
        x = (screen_width / 2) - (200 / 2)
        y = (screen_height / 2) - (100 / 2)
        self.geometry("+%d+%d" % (x, y))

    def close_dialog(self, result):
        self.result = result
        self.destroy()

      # usage
      #root = tk.Tk()
      #root.withdraw()

      #dialog = CustomDialog(root, title="Confirmation", message="This playlist already exist do you want to overwrite it?")
      #root.wait_window(dialog)

      #answer = dialog.result
      #root.destroy()

def debug_out(debug_val,debug_line):
    # usage example : debug_out(1,[" category_counts:{}, fractions:{}",category_counts, fractions])
    # debug_line is a list of values. "debug_line[0]"" is the message string and the remaining values 
    # are the values to be formatted into the message string.
    global starting_stack_depth
    if debug_val <= debug_level:
      # Get the name of the calling function for level 1 debug messages
      function_name = inspect.stack()[1][3].upper() if debug_val == 1 else ""
      
      # create an indentation string based on the current stack depth
      current_stack_depth = len(inspect.stack())
      depth = current_stack_depth - starting_stack_depth
      indent = ' ' * (depth - 1) * 5      

      # separate the message from the values to be formatted into the message
      message, *values = debug_line
      
      spaces = ' ' * debug_val
      message = spaces + message
    
      #formatted_debug_message = indent + function_name + " " + message.format(*map(str, values))
      formatted_debug_message = indent + function_name + " " + message.format(*values)
      
      logging.debug(formatted_debug_message)
      

def category_distribution(c_pct, playlist_tot_songs):
    """
    This function calculates the distribution of songs across different categories.

    Parameters:
    c_pct (list): A list of percentages, each representing the percentage of songs for a category.
    playlist_tot_songs (int): The total number of songs in the playlist.

    Returns:
    category_distribution_list (list): A list representing the distribution of songs. Each entry in the list is a string representing a category.
    """
    # Initialize an empty list to store the resulting distribution and a debug list
    category_distribution_list = []
    category_distribution_cnts = []
    
    # The following line calculates the number of songs for each category based on the percentage provided in 
    # 'c_pct' and the total number of songs in the playlist. It creates a list 'category_counts' where 
    # each item is the calculated number of songs for a category.
    category_counts = [int((int(percentage) / 100) * playlist_tot_songs) for percentage in c_pct]

    # Create a list of the initial fractions for each category 
    fractions = [1 / count for count in category_counts]
    debug_out(1,[" category_counts:{}, fractions:{}",category_counts, fractions])

    # Loop to generate the category_distribution_list. 
    while len(category_distribution_list) < playlist_tot_songs:
        # Find the index of the category with the lowest fraction
        min_fraction_index = np.argmin(fractions)
        debug_out(2,[" min_fraction_index:{}, fractions:{}",min_fraction_index, fractions])
        
        # Calculate the total count for the selected category
        category_count = category_counts[min_fraction_index]
                      
        current_count = len([entry for entry in category_distribution_list if categories[min_fraction_index] in entry])
          
        # Update the fraction for the selected category
        fractions[min_fraction_index] += 1 / category_count
        
        # Add the entry to the result list
        category_distribution_list.append(f"{categories[min_fraction_index]}")
        category_distribution_cnts.append(f" {current_count + 1} of {category_count}")


    return(category_distribution_list)

      
def main(usrname, misc, cat_dict_list, create_playlst): 
    # Accepts a configuration dictionary as input.
    # Sets up the database connection.
    # Updates the database to ensure that all tracks are eligible for playlist selection.
    # Iterates through the desired number of tracks for the playlist.
    # For each track, it selects a track from a specific category, ensuring that the same artist or category is not repeated too quickly.
    # Updates track and category counters to control repeat intervals.
    # Records track information in the playlist.
    global df, username, categories, debug_level, playlist_type, tracks_view, create_playlist, repeat, last_song, starting_stack_depth, cat_idx, failed_selection_list
    starting_stack_depth = len(inspect.stack()) 
    last_song = " "
    #misc, category = itemgetter('misc','categories')(config)
    debug_level=int(misc['debug_lvl'])
    debug_out(1,["{} Passed Dictionary:{},{}",datetime.now(),misc,cat_dict_list])
    playlist_name = misc['playlist_name']
    playlist_lgth = misc['playlist_lgth']
    playlist_type = misc['playlist_type']
    
    # Create variables to be used as global from the passed parms
    create_playlist = create_playlst
    username=usrname

    #cat_dict_list=categories
    categories = []
    cat_wildcard = []
    c_pct = []
    cat_rpt_list = []
    ra_playcnt = []
    failed_selection_list = [0,0,0,0,0,0]
    if playlist_type == 'ktunes':
      tracks_view = 'tracks_ktunes'
    else:
      tracks_view = 'tracks_itunes'

    # Connect to db
    conn = sqlite3.connect('kTunes.sqlite')
    sql_stmnt = conn.cursor()

    # Create a temporary table
    sql_stmnt.execute('''CREATE TEMPORARY TABLE playlist_song_play_counts 
                     (song TEXT, artist_common_name TEXT, playlist_play_cnt INTEGER, 
                     PRIMARY KEY(song, artist_common_name))''')


    # First create list for each item in the cat_dict_list list
    # Next reset the category names in the tracks table to their original values
    # Then, if its the first category, create the 'RecentAdd' category and move tracks to it based on the min play count
    # and move tracks to the 2nd category based on the max play count.
    for i, category in enumerate(cat_dict_list):
        categories.append(category['name'])
        cat_wildcard.append(category['wild_card'])
        ra_playcnt.append(category['ra_playcnt'])
        c_pct.append(category['pct'])
        cat_rpt_list.append(category['repeat'])

        # Previous playlist may have changed the category of some tracks. We need to reset them to their original values.
        sql_stmnt.execute('''update tracks set category = ? where genre like ? COLLATE NOCASE''',(categories[i],cat_wildcard[i],))

        if i == 1:
          # The first category can contains a min:max play count value. If there it will do two things:
          # 1 - The min value will be used to create a new category. It will be carved out of the 
          #     first category. Tracks with less plays than 'min' will be moved to the new category.
          # 2 - The max value will be used to determine which tracks from the first category should be 
          #     moved to the second category. Tracks with more plays than 'max' will be moved to the 2nd category.
          recentadd_play_cnt = ra_playcnt[i]
          debug_out(2,["recentadd_play_cnt:{}",recentadd_play_cnt])
          debug_out(3,["create RecnetAdd cat with play_cnt: {}",recentadd_play_cnt])
          sql_stmnt.execute('''update tracks set category = 'RecentAdd'
                          where category = ? COLLATE NOCASE
                            and play_cnt <= ?''',(categories[i], recentadd_play_cnt,))
          recentadd_count = sql_stmnt.rowcount  # Get the number of rows updated
          debug_out(2,["Number of tracks updated to RecentAdd: {}",recentadd_count])
          
        if i == 2:
          #debug_out(2,["Update tracks from 1st category to 2nd category if play_cnt>: {}",in_rot_play_cnt])
          #sql_stmnt.execute('''update tracks set category = ?
          #                where category = ? COLLATE NOCASE
          #                  and play_cnt > ?''',(categories[i], categories[i - 1], in_rot_play_cnt,))
          
          debug_out(2,["Update tracks from 'Latest' category to 'InRot' category if date_added is more than 18 months ago"])
          
          # Get the date 18 months ago
          eighteen_months_ago = (datetime.now() - timedelta(days=int(18*30.44))).strftime('%Y-%m-%d')

          sql_stmnt.execute('''update tracks set category = ?
                              where category = ? COLLATE NOCASE
                              and date_added <= ?''',(categories[i], categories[i - 1], eighteen_months_ago,))
          
          inrot_count = sql_stmnt.rowcount  # Get the number of rows updated
          debug_out(2,["Number of tracks updated to InRot: {}",inrot_count])    

    # Now need to iterate over the categories one more time to get the total number of tracks in each category
    # since they may have just been updated in the prior loop
    for i in range(len(categories)):
      sql_stmnt.execute('''select count(*) from tracks
                            where category=?''',(categories[i],))
      row=sql_stmnt.fetchone()
      tot_c_trk_cnt[i]=row[0]
 
    playlist_tot_songs=round(int(playlist_lgth) * 60 / 4) # avg song is 4 minutes

    cat_song_cnt_list = [round(playlist_tot_songs * float(c_pct[i]) / 100) for i in range(len(c_pct)) if float(c_pct[i]) > 0]
    
    """
    The variable 'cat_inv_pct' represents the inverse percentage of the number of songs a category should have
    in a playlist. For instance, if a playlist should contain 125 songs from the first category, 
    the 'cat_inv_pct' for this category would be calculated as (1/125)*100, which equals 0.8. 
    This value helps in determining the appropriate distribution of songs from different categories 
    in the playlist.

    The variable 'tot_cat_inv_pct' is initially set to the calculated 'cat_inv_pct' values. 
    As the playlist is being constructed, 'tot_cat_inv_pct' is used to keep a running total of the 
    'cat_inv_pct' for each category. By the time the playlist is fully built, the sum of 'cat_inv_pct' 
    for each category should be equal and match the total count of the playlist. This ensures a balanced 
    and proportional distribution of songs from each category in the playlist.
    """
    cat_inv_pct = [100/cat_song_cnt_list[i] for i in range(len(cat_song_cnt_list))]
    
    debug_out(0,["INFO - Plylst Name:     {}", playlist_name])
    debug_out(0,["INFO - Plylst Lngth:    {} hours", playlist_lgth])
    debug_out(0,["INFO - Total Songs:     {}", playlist_tot_songs])
    debug_out(0,["INFO - Recentadd Date:  {}", recentadd_play_cnt])
    debug_out(0,["INFO - Create Playlist: {}", create_playlist])
    debug_out(0,["INFO - Debug Level:     {}", debug_level])
    debug_out(0,["INFO - # # # # # # # # # # # # # # # # # # # # # ","x"])
    debug_out(0,["INFO - Category   Pct  PlylstSongs Tot Songs cat_inv_pct"])
    debug_out(0,["INFO   ---------- ---- ----------- --------- -----------"])
    for x in range(len(categories)):
      debug_out(0,["INFO   {:10} {:3.0f} {:12} {:9} {:3.1f}",categories[x],float(c_pct[x]),cat_song_cnt_list[x],tot_c_trk_cnt[x],float(cat_inv_pct[x])])

    if not create_playlist:
      conn.commit()
      conn.close()
      return(playlist_tot_songs,cat_song_cnt_list,tot_c_trk_cnt, False)
    else:
      # check if playlist already exists
      sql_stmnt.execute('''select "x" from playlist where username = ? and playlist_nm = ?;''',(username, playlist_name,))
      if sql_stmnt.fetchone():
        # create the root TKinter window for display of the yes/no dialog
        root = tk.Tk()
        root.withdraw()  # hide main window
        
        dialog = CustomDialog(root, title="Confirmation", message="This playlist already exist do you want to overwrite it?")
        root.wait_window(dialog)
        answer = dialog.result
        root.destroy()
        print(answer)  # print the result for testing
        #answer = askyesno(title=None, message="This playlist already exist do you want to overwrite it?", parent=root)

        
        if answer:
          delete_stmt = '''delete from playlist where playlist_nm = ?;'''
          sql_stmnt.execute(delete_stmt,(playlist_name,))
          delete_stmt = '''delete from playlist_tracks where playlist_nm = ?;'''
          sql_stmnt.execute(delete_stmt,(playlist_name,))
          conn.commit
        else:
          return(playlist_tot_songs,cat_song_cnt_list,True)

      for x in range(len(categories)):
        insert_stmt='''insert or replace into playlist
                      (username, playlist_dt, playlist_nm, playlist_type, length,nbr_of_songs,recentadd_play_cnt,debug_level,category,pct,nbr_of_cat_playlist_songs,nbr_of_cat_songs)
                      values (?,?,?,?,?,?,?,?,?,?,?,?);'''
        sql_stmnt.execute(insert_stmt,(username,today_dt,playlist_name, playlist_type, playlist_lgth, playlist_tot_songs, recentadd_play_cnt, debug_level, categories[x], float(c_pct[x]),cat_song_cnt_list[x],tot_c_trk_cnt[x],))
      conn.commit
    
    def fetch_song_from_tbl(cat):
    
      # This function will determine the next eligible track for a given category.
    
      global artist, categories, cat_idx, itunes_artist, length, play_cnt, song, location, played_sw, cat_cnt, artist_cat_cnt, last_play_dt, csr_row_cnt, failed_selection_list
      
      curr_cat_idx = cat_idx
      # We'll try this category and if there are no eligible tracks in it, we'll try the next category:
      while cat_idx <= curr_cat_idx + 1:
    
        debug_out(1,["Cat:{}, cnt:{}, cat_trk_cnt:{}, cat_idx{} ",cat, cnt,c_trk_cnter[cat_idx], categories, cat_idx])
        
        # Find rows that match this category and where the artist hasn't been played too recently. In this category or any others.
        join_and_where_stmnt = '''
           from ''' +  tracks_view  + ''' t 
            left join playlist_song_play_counts p on t.song = p.song and t.artist_common_name = p.artist_common_name
            where category = '{}'
              and artist_cat_cnt + {} <= cat_cnt 
              -- Excluding artists that have been played too recently in another category
              and t.artist_common_name not in 
                  (select distinct a.artist_common_name
                    from tracks a,
                          (select distinct artist_common_name from tracks where category = '{}') b
                    where a.artist_cat_cnt + {} > a.cat_cnt 
                      and a.category in ({})
                      and a.artist_cat_cnt != 0
                      and a.artist_common_name = b.artist_common_name )
              and played_sw = FALSE
            --order by last_play_dt
            ORDER BY COALESCE(p.playlist_play_cnt, 0), t.last_play_dt;
            '''.format(cat,  cat_repeat_interval, cat, cat_repeat_interval, ','.join(['?' for _ in categories]))
        
        sql =  '''select t.song, t.artist_common_name artist, t.artist itunes_artist, last_play_dt, played_sw, cat_cnt, artist_cat_cnt, rating, length, play_cnt, location 
                ''' + join_and_where_stmnt
        
        # I'll need the row count and unfortunetly rowcount is not reliable on select statments, only on CRUD, so I'll have to do a count(*)
        sql2 = '''select count(*) cursor_cnt
                ''' + join_and_where_stmnt
        cat_cur.execute(sql,categories)
        
        # If a category doesn't have enough songs to match nbr_of_<cat>_songs then when we get to the end we need to 
        # reset that cat and start from its beginning.
        result = cat_cur.fetchone()
        if result is not None:
          song, artist, itunes_artist, last_play_dt, played_sw, cat_cnt, artist_cat_cnt, rating, length, play_cnt, location = result
          break # No need to try the next category
        else: 
          # There were no records returned from the cursor so we need to resetting the played_sw so all recs will be eligible again.
          debug_out(0,["INFO - Processed all {} tracks. Need to start over. Cnt:{}. c_trk_cnter:{}", cat, cnt, c_trk_cnter[cat_idx]])
          if debug_level>0:
            f3.write("Reseting {} cursor after {} {} tracks".format(cat,c_trk_cnter[cat_idx],cat) + "\n")

          sql_stmnt.execute('update tracks set played_sw = FALSE  where category = ?;',(cat,))
          conn.commit
          # Reopening cursor after reset
          cat_cur.execute(sql,categories)
          result = cat_cur.fetchone()
          if result is not None:
            song, artist, itunes_artist, last_play_dt, played_sw, cat_cnt, artist_cat_cnt, rating, length, play_cnt, location = result
            break # Added 4/15/2024 - No need to try the next category
          else: 
            debug_out(1,["Cursor did not return any rows after reset. Will try next category. SQL statement was {}", sql])
            # No songs are eligible for this category so we'll try the next category. Hopefully the next time we try one will be eligible.
            failed_selection_list[cat_idx] += 1
            cat_idx += 1 
            cat = categories[cat_idx]
      
      cat_cur.execute(sql2,categories)
      csr_row_cnt=cat_cur.fetchone()
      
      debug_out(3,["Cursor returned ktunes_artist:{}, itunes_artist:{}, artist_cat_cnt:{}, cat_cnt:{}, song:{}, eligble rows:{}",artist, itunes_artist, artist_cat_cnt, cat_cnt, song, str(csr_row_cnt)])
      f3.write(" Selected:{}, Song:{}, cat:{}, artist_cat_cnt, cat_cnt".format(artist, song, cat, artist_cat_cnt, cat_cnt) + "\n")

    def get_track_for_category(cat, cnt):
      # The get_track_for_category function is used to get a single track for a given category. 
      # The function first calls the fetch_song_from_tbl function to retrieve a cursor of all the tracks for the given category. 
      # It then writes the current track to the playlist file and updates the database to mark this track as played.
      # The function also updates the cat_cnt and artist_cat_cnt fields in the database for this track’s category and artist. 
      # These fields are used to ensure that each category and artist is played fairly and that no two tracks from the same
      # artist and category are played more frequently than the repeat count.
      # If an artist is in multiple categories 
      global artist_cat_cnt, cat_cnt, last_song
      return_val='Continue'
      debug_out(1,["Category:{}, cnt:{}",cat, cnt])
      
      fetch_song_from_tbl(cat)
          
      debug_out(2,["get_track_for_category - writing to playlist. Genre:{}, c_trk_cnter:{}, cat_repeat_interval:{}",cat,c_trk_cnter[cat_idx],cat_repeat_interval])
      line1='#EXTINF: ' + str(length) + ',' + artist + " - " + song 
      f2.write(line1 + "\n")
      f2.write(location + "\n")
      #Don't wannan here this song again until we get through all other songs in the category so set played_sw to TRUE
      sql_stmnt.execute('''update tracks
                              set played_sw = TRUE
                                where artist_common_name = ?
                                  and song = ?;''',(artist,song,))
      # Update the temporary table with the play count for this song. This table helps insure we select all songs evern after a reset of the played_sw
      sql_stmnt.execute('''
          INSERT OR REPLACE INTO playlist_song_play_counts (song, artist_common_name, playlist_play_cnt)
          VALUES (?, ?, COALESCE((SELECT playlist_play_cnt FROM playlist_song_play_counts WHERE song = ? AND artist_common_name = ?), 0) + 1)
          ''', (song, artist, song, artist))
      
      if cat in [categories[1], categories[2]]:
        cat_val = f"('{categories[1]}', '{categories[2]}')"
      else:
        cat_val= "('" + cat + "')"
      
      stmnt='''update tracks set cat_cnt = cat_cnt + 1 where category in ''' + cat_val
      sql_stmnt.execute(stmnt)
      rows_updated = sql_stmnt.rowcount 

      stmnt='''select cat_cnt, artist_cat_cnt from tracks where category in ''' + cat_val
      sql_stmnt.execute(stmnt)
      row=sql_stmnt.fetchone()
      if row is not None:
        cat_cnt, artist_cat_cnt = row
      else:
        row=['blank',0]
        
      debug_out(2,[" After update of cat_cnt. Updated {} rows. Row = {}", rows_updated, row])
                   
      # 6/22/23 - I had a bug where I was running out of 'album' tracks in a playlist. It appears it was because in the following statement I'd
      # commented out the 'and category in cat_val' part. This meant everytime an artist was selected, it said could not play another 'album'
      # track from that artist till we played at least 50 other album tracks. But we never got to 50 album tracks. They had all been marked to not play
      # till 50 tracks by the 44th album track. So I'm uncommenting the 'catatory' check. I originally commented it out in January of 23 to fix the issue 
      # where I was getting artist who where in multiple categories to be played too frequently (like Hippo Campus)

      # I'm using ? instead of {} and format because some of the artist names have quotes in them and using {}.format does not seem to handle this
      stmnt = "update tracks set artist_cat_cnt = cat_cnt where artist_common_name = ? and category in {}".format(cat_val)
      f3.write(" update statement =:{}, params = {} /n".format(stmnt, artist))
      sql_stmnt.execute(stmnt, (artist,))
      rows_updated = sql_stmnt.rowcount 

      stmnt='select cat_cnt, artist_cat_cnt from tracks where artist_common_name = ? and category in ' + cat_val
      sql_stmnt.execute(stmnt,(artist,))
      row=sql_stmnt.fetchone()
      if row is None:
        row=['blank',0]
      disp_cat_cnt, disp_artist_cat_cnt = row
      debug_out(2,[" After update of artist_cat_cnt. Rows updated:{}, artist_cat_cnt:{}, cat_cnt:{}",rows_updated,disp_artist_cat_cnt,disp_cat_cnt])

      stmnt='''insert or replace into playlist_tracks
                      (username,playlist_dt,playlist_nm,track_cnt,artist, artist_common_name, song, category,length,play_cnt,last_play_dt,cat_cnt,artist_cat_cnt)
                      values (?,?,?,?,?,?,?,?,?,?,?,?,?);''' 
      sql_stmnt.execute(stmnt,(username,today_dt,playlist_name,cnt,itunes_artist,artist,song,cat,length/1000/60,play_cnt, last_play_dt,cat_cnt,artist_cat_cnt,))
      
      if debug_level>9:
        print("artist",artist, " song",song,  "length",length, "cat_repeat_interval", cat_repeat_interval,"cnt",cnt,"cat_cnt",cat_cnt)
        sng_lngth = str(round(length/1000/60,2))
        frmt="{:<20s}{:<20s} L-{:5s} C:{:11s} R:{:<3d} cnt:{:<3d} c-cnt:{:<3d} ac-cnt:{:<3d} csr-cnt:{:<4s} lp-dt:{:<13s} {:<9s}"
        f3.write(frmt.format(artist[0:20], song[0:20], str(round(length/1000/60,2)), cat, cat_repeat_interval,cnt, cat_cnt,artist_cat_cnt,str(csr_row_cnt[0]),str(last_play_dt)[0:12], str(play_cnt)) + "\n")
                              
      debug_out(2,[" End - return_val={}",str(return_val)])
      conn.commit

      return(return_val)
    

    # MAIN PROCESSING STARTS HERE

    cat_cur = conn.cursor()
    f2 = open(playlist_name+".m3u", "w")
    f2.write("#EXTM3U" + "\n")
    #if debug_level>0:
    f3 = open("playlist_debug.log", "w")

      
    # Need to set last_play_dt to 0 if its a brand new track
    sql_stmnt.execute('update tracks set last_play_dt = 0 where last_play_dt = "Unknown";')

    # Prior to (re)creating playlist need to set all tracks as eligble for selection.
    # We initialize cat_cnt to the repeat interval for the category. 
    # We set artist_cat_cnt to zero making all artist tracks for a category eligible for selection.
    
    for x in range(len(categories)):
      sql_stmnt.execute('''update tracks set played_sw=FALSE, artist_cat_cnt = 0, cat_cnt = ?
                          where category = ?;''',(cat_rpt_list[x],categories[x]))

    # Create initial list to be used to create the final playlist. Function will create equal distribution
    # of categories based on the percentage the user specified percentage for each category. 
    # Each entry is the category from which a song will be later selected..
    category_distribution_list = category_distribution(c_pct, playlist_tot_songs)
    
    
    debug_out(2,["Main Loop: about to create song distribution {}",category_distribution_list])
    # Now that we have the category distribution list we'll loop through it to create the playlist
    for cnt, cat in enumerate(category_distribution_list):
      cat_idx=categories.index(cat)
      cat_repeat_interval=cat_rpt_list[cat_idx]
      c_trk_cnter[cat_idx] += 1
      debug_out(2,[" Main Loop - cnt:{}, cat:{}, cat_repeat_interval:{}",cnt, cat, cat_repeat_interval])
      
      # call get_track_for_category with the current cat.
      result = get_track_for_category(cat,cnt)
      if result != 'Continue':
        debug_out(2,[" Main Loop, taking an early exit"])
        break
        
      

    debug_out(1,["End of process_db main cnt={}",cnt])
        

    conn.commit()
    conn.close()

    debug_out(0,["# # # # # # # # # # # # # # # # # # # # # "])
    debug_out(0,["# Script execution complete. Final track count={}, nbr_of_cat_song list = {}, tot_cat_tracks = {}",playlist_tot_songs,cat_song_cnt_list,tot_c_trk_cnt,"f"])
    debug_out(0,["# # # # # # # # # # # # # # # # # # # # # "])

    f2.close() # m3u file
    #if debug_level>0:
    f3.close() # m3u debug file
    

    return(playlist_tot_songs,cat_song_cnt_list,tot_c_trk_cnt,False,failed_selection_list)

    # End of "main" function

if __name__ == "__main__":
   main(dbug_lvl=5,c_pct=cat_pct,playlist_nm=playlist_name,playlist_lgth=playlist_length,create_plylist="Yes")  
  
   
