from flask import Flask, render_template, jsonify
import sqlite3

app = Flask(__name__)

@app.route("/config", methods=["GET", "POST"])
def create_playlist():
    pass

@app.route('/tracks')
def tracks():
    conn = sqlite3.connect('kTunes.sqlite')
    cursor = conn.cursor()

    # Get the total number of tracks
    cursor.execute('SELECT COUNT(*) FROM tracks')
    total_tracks = cursor.fetchone()[0]

    # Get the first 20 tracks
    cursor.execute('SELECT * FROM tracks LIMIT 20')
    tracks = cursor.fetchall()
    #print("Tracks=",tracks)

    return render_template('scroll.html', tracks=tracks, total_tracks=total_tracks)

@app.route('/load-more-tracks/<int:offset>')
def load_more_tracks(offset):
    conn = sqlite3.connect('kTunes.sqlite')
    cursor = conn.cursor()

    # Get the next 20 tracks starting from the given offset
    cursor.execute('SELECT * FROM tracks LIMIT 20 OFFSET ?', (offset,))
    tracks = cursor.fetchall()

    return jsonify({'html': render_template('tracks-list.html', tracks=tracks)})


if __name__ == '__main__':
    app.run(debug=True)
