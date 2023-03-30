from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

@app.route("/config", methods=["GET", "POST"])
def create_playlist():
    pass

# Helper function to get the total number of tracks in the database
def get_total_tracks():
    conn = sqlite3.connect('kTunes.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM tracks')
    total_tracks = cursor.fetchone()[0]
    conn.close()
    return total_tracks

# Helper function to get a page of tracks from the database
def get_tracks(start, limit):
    conn = sqlite3.connect('kTunes.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT artist, song, category, album, play_cnt, last_play_dt, date_added FROM tracks ORDER BY artist LIMIT ?, ?', (start, limit))
    tracks = cursor.fetchall()
    conn.close()
    return tracks

# Route for the tracks page
@app.route('/tracks')
def tracks():
    # Get the page number from the request args, default to 1 if not present
    page = request.args.get('page', 1, type=int)
    # Set the number of tracks per page
    per_page = 20
    # Calculate the starting index of the tracks for the current page
    start = (page - 1) * per_page
    # Get the total number of tracks in the database
    total_tracks = get_total_tracks()
    # Get the tracks for the current page
    tracks = get_tracks(start, per_page)
    # Calculate the total number of pages based on the number of tracks per page
    total_pages = (total_tracks + per_page - 1) // per_page
    # Render the template with the tracks and pagination information
    print("before render_template, tracks=",tracks)
    return render_template('scroll.html', tracks=tracks, total_pages=total_pages)

if __name__ == '__main__':
    app.run(debug=True)
