import sqlite3
#from tkinter.tix import ROW
from flask import Flask,redirect, url_for, request, render_template
from werkzeug.exceptions import abort
import process_db

# kkrug - variables prefixed with t_* are to help me remember these are being passed to a template.

# Create your Flask app instance with the name "app". Pass it the special var __name__ that holds the name of the current Python module.
# Often the python module is also named "app" but does not need to be. If you use another name then you need to tell flask
# what name you used when you start flask by exporting the FLASK_APP variable.
app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('iTunes.2.0.sqlite')
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

@app.route('/newplaylist',methods = ['POST', 'GET'])
def create_playlist_form():
   if request.method == "POST":
      
      pcts = [
              float(request.form["latest_pct"]),
              float(request.form["in_rot_pct"]),
              float(request.form["other_pct"]),
              float(request.form["album_pct"]),
              float(request.form["old_pct"])
             ]
      playlist_name=request.form["playlist_name"]
      playlist_length=request.form["playlist_length"]
      #genre_pct=[str(.16),str(.44),str(.27),str(.08),str(.05)]
      total_songs,nbr_of_genre_songs=process_db.main(1,pcts,playlist_name,playlist_length)
      nbr_of_latest_songs=nbr_of_genre_songs[0]
      nbr_of_in_rot_songs=nbr_of_genre_songs[1]
      nbr_of_other_songs=nbr_of_genre_songs[2]
      nbr_of_album_songs=nbr_of_genre_songs[3]
      nbr_of_old_songs=nbr_of_genre_songs[4]
      playlist_name="<new playlist_name>"
      #playlist_length=request.form["playlist_length"]
      latest_pct=request.form["latest_pct"]
      in_rot_pct=request.form["in_rot_pct"]
      other_pct=request.form["other_pct"]
      old_pct=request.form["old_pct"]
      album_pct=request.form["album_pct"]
      msg="Playlist "+request.form["playlist_name"]+" (re)created with the following song counts"
      return render_template("new_playlist.html",playlist_name=playlist_name, 
                                                 playlist_length=playlist_length,
                                                 latest_pct=latest_pct,
                                                 in_rot_pct=in_rot_pct,
                                                 other_pct=other_pct,
                                                 old_pct=old_pct,
                                                 album_pct=album_pct,
                                                 msg=msg,
                                                 total_songs=" Total Songs - "+ str(total_songs),
                                                 nbr_of_latest_songs="  Latest - "+ str(nbr_of_latest_songs),
                                                 nbr_of_in_rot_songs="  In Rot - "+ str(nbr_of_in_rot_songs),
                                                 nbr_of_other_songs="  Other - "+ str(nbr_of_other_songs),
                                                 nbr_of_old_songs="  Old - "+ str(nbr_of_old_songs),
                                                 nbr_of_album_songs="  Album - "+ str(nbr_of_album_songs))
   else:
      playlist_name="<new playlist_name>"
      playlist_length=2500
      latest_pct=.16
      in_rot_pct=.44
      other_pct=.27
      old_pct=.08
      album_pct=.05
      return render_template("new_playlist.html",playlist_name=playlist_name, 
                                                 playlist_length=playlist_length,
                                                 latest_pct=latest_pct,
                                                 in_rot_pct=in_rot_pct,
                                                 other_pct=other_pct,
                                                 old_pct=old_pct,
                                                 album_pct=album_pct,
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
    app.run()
