import sqlite3
#from tkinter.tix import ROW
from flask import Flask,redirect, url_for, request, render_template
from werkzeug.exceptions import abort
import load_xml
from datetime import datetime,timedelta
import process_db

# Create your Flask app instance with the name "app". Pass it the special var __name__ that holds the name of the current Python module.
# Often the python module is also named "app" but does not need to be. If you use another name then you need to tell flask
# what name you used when you start flask by exporting the FLASK_APP variable.
app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('kTunes.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=["GET", "POST"])
def enter_data():
   if request.method == "POST":
      artist = request.form["artist"]
      artist_tracks = get_artist_tracks(artist)
      return render_template('artists.html', t_tracks=artist_tracks, artist=artist)
   else:
      return render_template('menu.html')

@app.route('/index')
def index():
    conn = get_db_connection()
    artist_cnt = conn.execute('select artist, max(last_play_dt) last_play_dt,  count(*) cnt from tracks group by artist').fetchall()
    conn.close()
    #print("Index Row=",artists)
    return render_template('index.html', t_artist_cnt=artist_cnt)

def get_artist_tracks(artist):
    #print('In get_artist',artist)
    conn = get_db_connection()
    a = "%" + artist + "%"
    artist_tracks = conn.execute('SELECT artist, song, genre, last_play_dt, rating, cnt, repeat_cnt FROM tracks WHERE artist like ?',
                        (a,)).fetchall()
    conn.close()
    if artist_tracks is None:
        print("Uh oh - nothing to post")
        abort(404)
    return artist_tracks

@app.route('/artist/<artist>', methods=["GET", "POST"])
def disp_artist(artist):
   if request.method == "POST":
      artist = request.form["artist"]
      artist_tracks = get_artist_tracks(artist)
   else:
      artist_tracks = get_artist_tracks(artist)
   return render_template('artists.html', t_tracks=artist_tracks, artist=artist)

# From main screen if you choose create playlist, the form will post which allows process_db.py to be executed.
@app.route('/newplaylist',methods = ['POST', 'GET'])
def create_playlist_form():
   if request.method == "POST":
      
      pcts = [
              float(0),
              float(request.form["latest_pct"]),
              float(request.form["in_rot_pct"]),
              float(request.form["other_pct"]),
              float(request.form["old_pct"]),
              float(request.form["album_pct"])
             ]
      playlist_name=request.form["playlist_name"]
      playlist_length=request.form["playlist_length"]
      if request.form.get('create_playlist'):
        create_playlist="Yes"
      else:
         create_playlist="No"
      create_recentadd_cat="No"
      if request.form.get("x"):
         create_recentadd_cat="Yes"
         recentadd_dt=request.form["recentadd_dt"]
         weighting_pct=request.form["weighting_pct"]
      else:
         recentadd_dt=""
         weighting_pct=""
      
      # Calling process_db.main
      total_songs,nbr_of_genre_songs=process_db.main(0,
                                                      ["RecentAdd","Latest","In Rot","Other","Old","Damaged"],
                                                      pcts,
                                                      playlist_name,
                                                      playlist_length,
                                                      create_recentadd_cat, recentadd_dt, weighting_pct,
                                                      create_playlist)
      nbr_of_recentadd_songs=nbr_of_genre_songs[0]
      nbr_of_latest_songs=nbr_of_genre_songs[1]
      nbr_of_in_rot_songs=nbr_of_genre_songs[2]
      nbr_of_other_songs=nbr_of_genre_songs[3]
      nbr_of_album_songs=nbr_of_genre_songs[4]
      nbr_of_old_songs=nbr_of_genre_songs[5]
      playlist_name=request.form["playlist_name"]
      latest_pct=request.form["latest_pct"]
      in_rot_pct=request.form["in_rot_pct"]
      other_pct=request.form["other_pct"]
      old_pct=request.form["old_pct"]
      album_pct=request.form["album_pct"]
      recentadd_dt=request.form["recentadd_dt"]
      weighting_pct=request.form["weighting_pct"]
      msg="Playlist "+request.form["playlist_name"]+" (re)created with the following song counts"
      return render_template("new_playlist.html",playlist_name=playlist_name, 
                                                 playlist_length=playlist_length,
                                                 latest_pct=latest_pct,
                                                 in_rot_pct=in_rot_pct,
                                                 other_pct=other_pct,
                                                 old_pct=old_pct,
                                                 album_pct=album_pct,
                                                 create_recentadd_cat=create_recentadd_cat,
                                                 recentadd_dt=recentadd_dt,
                                                 weighting_pct=weighting_pct,
                                                 create_playlist="Yes",
                                                 msg=msg,
                                                 total_songs=" Total Songs - "+ str(total_songs),
                                                 nbr_of_recentadd_songs="  Recent Add - "+ str(nbr_of_recentadd_songs),
                                                 nbr_of_latest_songs="  Latest - "+ str(nbr_of_latest_songs),
                                                 nbr_of_in_rot_songs="  In Rot - "+ str(nbr_of_in_rot_songs),
                                                 nbr_of_other_songs="  Other - "+ str(nbr_of_other_songs),
                                                 nbr_of_old_songs="  Old - "+ str(nbr_of_old_songs),
                                                 nbr_of_album_songs="  Album - "+ str(nbr_of_album_songs))  
   else:
      playlist_length=2500
      latest_pct=35
      in_rot_pct=25
      other_pct=15
      old_pct=15
      album_pct=10
      weighting_pct=20
      create_recentadd_cat="No"
      curr_dt = datetime.now() 
      curr_dt = curr_dt.strftime("%m%d%y")
      playlist_name="p" + "_" + curr_dt + "_" + str(latest_pct) + "." + str(in_rot_pct) + "." + str(other_pct) + "." + str(old_pct) + "." + str(album_pct)
      try:
        recentadd_dt
      except NameError:
        six_months_ago = datetime.now() - timedelta(days=180)
        recentadd_dt=six_months_ago.strftime("%Y-%m-%d")
      print("recentad_dt=",recentadd_dt)
      return render_template("new_playlist.html",playlist_name=playlist_name, 
                                                 playlist_length=playlist_length,
                                                 latest_pct=latest_pct,
                                                 in_rot_pct=in_rot_pct,
                                                 other_pct=other_pct,
                                                 old_pct=old_pct,
                                                 album_pct=album_pct,
                                                 create_recentadd_cat=create_recentadd_cat,
                                                 recentadd_dt=recentadd_dt,
                                                 weighting_pct=weighting_pct,
                                                 msg="Enter data and hit Submit to create new playlist")

@app.route('/result',methods = ['POST', 'GET'])
def result():
   if request.method == 'POST':
      result = request.form
      return render_template("result.html",result = result)

@app.route('/blog/<int:postID>')
def show_blog(postID):
   print('Blog id=',postID)
   return 'Blog Number %d' % postID

@app.route('/user/<playlist_tot_songs>')
def hello_user(playlist_tot_songs):
   if playlist_tot_songs =='admin':
      return redirect(url_for('hello_admin'))
   else:
      return redirect(url_for('hello_guest',guest = playlist_tot_songs))

@app.route('/success/<playlist_tot_songs>')
def success(playlist_tot_songs):
   return 'Number of minutes in playslist is %s' % playlist_tot_songs

@app.route('/login',methods = ['POST', 'GET'])
def login():
   if request.method == 'POST':
      tot_nbr = request.form['nbr']  # nbr is variable playlist_tot_songs on html form
      return redirect(url_for('success',playlist_tot_songs = tot_nbr))
   else:
      tot_nbr = request.args.get('nbr') # nbr is variable playlist_tot_songs on html form
      return redirect(url_for('success',playlist_tot_songs = tot_nbr))

if __name__ == '__main__':
    app.run(debug=True)
