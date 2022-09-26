import sqlite3
from ssl import ALERT_DESCRIPTION_CLOSE_NOTIFY
conn = sqlite3.connect('iTunes.sqlite')
cur = conn.cursor()
global select_return
#artist="Smash Mouth"
#genre = 'Other than New'
#cnt=3

last_played_cur = conn.cursor()


debug_level = 4
debug_to_file = True
if debug_to_file == True:
  df = open("debug_out.txt", "w")

spc = {}
spc[1] = ""
spc[2] = " "
spc[3] = "  "
spc[4] = "   "

def debug_out(debug_val,debug_line):
  if debug_val <= debug_level:
    print(spc[debug_val],debug_line)
    if debug_to_file == True:
      tup1 = (debug_line)
      strg = spc[debug_val]
      for item in tup1:
        item = str(item)
        strg = strg + item + ", "
      df.write(strg + "\n")
upd_cur = conn.cursor()
      
in_rot_cur = conn.cursor()
def open_genre_track_cursors():
  debug_out(4,["open_genre_track_cursors:",cnt])
  in_rot_cur.execute('select * from in_rot_tracks where last_played <= ? order by last_play_dt',(cnt,))


def fetch_genre_cur():
  global artist, length, song, location,cnt
  return_val=False  
  in_rot_cur.execute('select * from in_rot_tracks where last_played <= ? order by last_play_dt',(cnt,))
  song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=in_rot_cur.fetchone() 
  debug_out(2,["fetch_genre_cur",cnt,artist,song])

  upd_cur.execute('''update in_rot_tracks set last_played=12 where artist= 'The Decemberists';''')   
  conn.commit 

  cnt=0
  in_rot_cur.execute('select * from in_rot_tracks where last_played > ? order by last_play_dt',(cnt,))
  song,artist, last_play_dt, last_played, rating, length, repeat_cnt, location=in_rot_cur.fetchone() 
  debug_out(2,["fetch_genre_cur",cnt,artist,song])

  #upd_cur.execute('''update in_rot_tracks set last_played=12 where artist= 'The Decemberists';''')   
  conn.commit 

  return_val=True
  return False

with open(r"process_db_genre_fin_order.txt", 'r') as f1:
 for cnt, line in enumerate(f1):
  genre=line.strip()
  debug_out(1,["Main Loop:",str(cnt), genre,ALERT_DESCRIPTION_CLOSE_NOTIFY])
  while fetch_genre_cur() == True:
    #pass
    debug_out(1,["End - Main Loop"])
    #exit

debug_out(1,["End of process_db_genre_file_order.txt. cnt=",cnt])

conn.commit()
conn.close()
 
