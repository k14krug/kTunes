from flask import Flask, render_template, request, Blueprint
from flask import jsonify
from flask import flash
import configparser
import sqlite3
import random
import os
import shutil
import process_db 
import load_xml
from validate_playlist import validate_playlist

app = Flask(__name__)
app.secret_key = 'ktunes secret key #8Ghj^&*'

# Define the blueprint
ktunes = Blueprint('ktunes', __name__, url_prefix='/ktunes')

# Database
DATABASE = 'kTunes.sqlite'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Define the path to the config file
config_path = 'ktunes.ini'
config = configparser.ConfigParser()
config.read(config_path)
if not config.has_section("misc"):
    print("config doesn't have misc section, gonna write out a default one")
    default_config = {
        "misc": {
            "playlist_name": "",
            "playlist_lgth": "",
            "itunes_xml_file": 'iTunesMusicLibrary.xml',
            "debug_lvl": ""
        },
        "category.Latest": {
            "pct":'30',
            "artist_repeat": '21',
            "min_max_playcnt": '20:60',
            "wild_card": 'Latest%%'
        }
    }
    print("before reading default_config")
    config.read_dict(default_config)
    with open(config_path, "w") as config_file:
        config.write(config_file)
    


# List of background images
background_images = [
    'zPiecesOfEight1.jpg',
    'zPiecesOfEight2.jpg',
    'zPiecesOfEight3.jpg',
    'zPiecesOfEight4.jpg',
    'zPiecesOfEight5.jpg',
    ]
# Select a random background image from the list
selected_image = random.choice(background_images)

# Generate the URL for the selected image
background_image_url = f"/static/images/{selected_image}"

playlist_cat_cnt = [0,0,0,0,0,0]

# Function to query a table with filters and paginate the result set
def query_table(**kwargs):
    db = get_db_connection()
    count_query = f"SELECT count(*) FROM ({kwargs['query']})"
    #print("count_query=",count_query)
    cursor = db.execute(count_query)
    count = cursor.fetchone()[0]
    offset = (kwargs['page'] - 1) * kwargs['per_page']
    limit = kwargs['per_page']
    order_by_str = ', '.join(kwargs['order_by_cols'])
    query = f"{kwargs['query']} ORDER BY {order_by_str}  LIMIT ?, ?"
    cursor = db.execute(query, (offset, limit))
    tracks = cursor.fetchall()
    cursor.close()
    return tracks, count

@ktunes.route('/settings', methods=['GET', 'POST'])
def settings():
    config.read(config_path)
    message = None
    file_list = []
    itunes_lib_file = request.form.get('itunes_lib')
    directory_path = config['misc']['itunes_dir']
    # Convert the Windows-style path to a Unix-style path
    linux_directory_path = directory_path.replace('\\', '/').replace('C:', '/mnt/c')
    if request.method == 'GET':
        print("get")
        # Get a list of files in the directory
        file_list = os.listdir(linux_directory_path)
        itunes_lib_file = config['misc']['itunes_lib']

    if request.method == 'POST':
        print("post")
        config['misc']['debug_lvl'] = request.form.get('debug_lvl')
        directory_path = request.form.get('itunes_dir')
        config['misc']['itunes_dir'] = directory_path
        print("itunes_lib_file=",itunes_lib_file)
        if directory_path:
            # Convert the Windows-style path to a Unix-style path
            linux_directory_path = directory_path.replace('\\', '/').replace('C:', '/mnt/c')
            try:
              # Get a list of files in the directory
              file_list = os.listdir(linux_directory_path)
            except OSError:
                message = f'Error: The directory {directory_path} is invalid.'
            else:
                if itunes_lib_file:
                    config['misc']['itunes_lib'] = itunes_lib_file
                    with open(config_path, "w") as config_file:
                        config.write(config_file)
                    message = f'Directory {directory_path}\{itunes_lib_file} was selected and copied to working dir'
                    # Copy the file to the current directory
                    current_directory = os.getcwd()
                    destination_path = os.path.join(current_directory, itunes_lib_file)
                    shutil.copyfile(os.path.join(linux_directory_path, itunes_lib_file), destination_path)
                else:
                    message = f'Choose the itunes library file from {directory_path}'
    return render_template('settings.html', config=config, message=message, file_list=file_list)

# route to create a new playlist
@ktunes.route("/cr_playlist", methods=["GET", "POST"])
def create_playlist():
    # Read the configuration file
    config.read(config_path)
    
    error_msg = ""
    success_msg = ""
    categories = []
    wild_card = []
    playlist_cat_cnt = []
    lib_cat_cnt = []
    category_repeat_interval = []
    total_songs = 0
    if request.method == "POST":  
        form_data = request.form
        # Retreive the form fields for the misc section of the configuration file
        config["misc"]["playlist_name"] = request.form["playlist_name"]
        config["misc"]["playlist_lgth"] = request.form["playlist_lgth"]
        #config["misc"]["debug_lvl"] = request.form["debug_lvl"]

        total_pct = 0
        category_names = []
        # artist_repeat value is the number of songs before an artist can repeat in a category (roughly)
        artist_repeat_values = []

        # Update category data with form data
        for i in range(len(request.form.getlist('name[]'))):
            category_dict = {
                'name': request.form.getlist('name[]')[i],
                'wild_card': request.form.getlist('wild_card[]')[i] if i < len(request.form.getlist('wild_card[]')) else '',
                'min_max_playcnt': request.form.getlist('min_max_playcnt[]')[i] if i < len(request.form.getlist('min_max_playcnt[]')) else '',
                'pct': request.form.getlist('pct[]')[i] if i < len(request.form.getlist('pct[]')) else '',
                'repeat': request.form.getlist('repeat[]')[i] if i < len(request.form.getlist('repeat[]')) else ''
            }
                
            category_names.append(category_dict['name'])
            artist_repeat_values.append(int(category_dict['repeat']))
            
            # Append each category dictionary to the categories list
            categories.append(category_dict)

            # Add pct to total_pct
            total_pct += int(category_dict['pct'])

            # Create a unique section for each category to be written to the config file
            section_name = 'category.' + category_dict["name"]
            if not config.has_section(section_name):
                config.add_section(section_name)
            config.set(section_name, 'wild_card', category_dict["wild_card"].replace('%', '%%'))
            config.set(section_name, 'pct', category_dict["pct"])
            config.set(section_name, 'repeat', category_dict["repeat"])
            config.set(section_name, 'min_max_playcnt', category_dict["min_max_playcnt"])

        if total_pct != 100:
           error_msg = "# # # Category 'Percent' column must total 100 (current total is {}). Category configurations not saved. # # #.".format(total_pct)
        else:  
            # Write out the config file
            with open(config_path, "w") as config_file:
                config.write(config_file)
            
            submission_method = request.form.get("submissionMethod")

            if submission_method == "Button":
                # call process_db
                total_songs, playlist_cat_cnt, lib_cat_cnt, dup_playlist = process_db.main(categories=categories, misc=config['misc'],create_playlst=True)
                
                # Validate generated playlist
                validation_errors = validate_playlist(config['misc']['playlist_name'],category_names,artist_repeat_values)
                print("validation_errors",validation_errors)
                if validation_errors > 0:
                    error_msg = "# # # Playlist created but has {} validation error(s). # # #.".format(validation_errors)
                else:
                    success_msg = "Playlist created successfully with {} songs. ".format(total_songs)
            else:
                total_songs, playlist_cat_cnt, lib_cat_cnt, dup_playlist = process_db.main(categories=categories, misc=config['misc'],create_playlst=False)
                
            # Calculate the song repeat interval in hours for each category
            for i in range(len(playlist_cat_cnt)):
                category_repeat_interval.append(round(lib_cat_cnt[i] / playlist_cat_cnt[i] * total_songs * 4 / 60))
    else:
        # (re)read the configuration file
        config.read(config_path)
        categories = [] 

        # Loop through sections and create a dictionary for each category
        for section in config.sections():
            if section.startswith('category.'):
                category_dict = {
                    'name': section.split('.')[1],
                    'wild_card': config.get(section, 'wild_card').replace('*', '%'),
                    'pct': config.get(section, 'pct'),
                    'repeat': config.get(section, 'repeat'),
                    'min_max_playcnt': config.get(section, 'min_max_playcnt', fallback='')
                }
                categories.append(category_dict)
        
    return render_template("cr_playlist.html", endpoint='ktunes.playlist', categories=categories, config=config, total_songs=total_songs, track_counts_list=playlist_cat_cnt,tot_songs=lib_cat_cnt,repeat_interval=category_repeat_interval, error=error_msg, success=success_msg)
    
# Route to display the paginated table of playlist
@ktunes.route('/playlist', methods=['GET', 'POST'])
def playlist():
    q_dict = {}
    screen_height = request.args.get('screen_height', type=int)
    if screen_height:
        print("got a screen_height of",screen_height)
        max_rows_response = requests.get(f"{request.url_root}get_max_rows?screen_height={screen_height}")
        if max_rows_response.status_code == 200:
            max_rows = max_rows_response.json().get('max_rows')
            per_page = max_rows
        else:
            per_page = 20
    else:
        print("didn't get a screen height")
        per_page = request.args.get('per_page', 20, type=int)
    
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    
    q_dict['playlist'] = request.args.get('playlist', 'kTunes')
    q_dict['artist'] = request.args.get('artist', '')
    q_dict['song'] = request.args.get('song', '')
    q_dict['category'] = request.args.get('category', '')
    
    query = "SELECT playlist_nm, track_cnt, artist, song, category, play_cnt, strftime('%Y-%m-%d', last_play_dt) AS last_play_dt FROM playlist_tracks WHERE lower(playlist_nm) like '" + q_dict['playlist'].lower() + "%'"
    if q_dict['artist']:
        query += " AND lower(Artist) LIKE '%" + q_dict['artist'].lower() + "%'"
    if q_dict['song']:
        query += " AND lower(song) LIKE '%" + q_dict['song'].lower() +  "%'"
    if q_dict['category']:
        query += " AND category LIKE '%" + q_dict['category'].lower() + "%'"
    
    q_dict['query'] = query
    q_dict['order_by_cols'] = ['track_cnt']
    q_dict['per_page'] = per_page
    q_dict['page'] = page    
    
    tracks, count = query_table(**q_dict)
    total_pages = (count + per_page - 1) // per_page     
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)
    endpoint = 'ktunes.playlist' 
    template_name= 'playlist.html'
    return render_template('table_templ.html', template_name=template_name, endpoint=endpoint, tracks=tracks, count=count, total_pages=total_pages, page=page, per_page=per_page, start_page=start_page, end_page=end_page, q_dict=q_dict)#, background_image_url=background_image_url)


# Route to display the paginated table of tracks
@ktunes.route('/tracks', methods=['GET', 'POST'])
def tracks():
    q_dict = {}
    screen_height = request.args.get('screen_height', type=int)
    if screen_height:
        print("got a screen_height of",screen_height)
        max_rows_response = requests.get(f"{request.url_root}get_max_rows?screen_height={screen_height}")
        if max_rows_response.status_code == 200:
            max_rows = max_rows_response.json().get('max_rows')
            per_page = max_rows
        else:
            per_page = 20
    else:
        print("didn't get a screen height!")
        per_page = request.args.get('per_page', 20, type=int)
    
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    sort_column = request.args.get('sort', 'name')
    sort_direction = request.args.get('direction', 'asc')      
    if sort_column not in ['last_play_dt']:
        sort_column = ['artist', 'song']
    if sort_direction not in ['asc', 'desc']:
        sort_direction = 'asc'   
    
    q_dict['artist'] = request.args.get('artist', '')
    q_dict['song'] = request.args.get('song', '')
    q_dict['category'] = request.args.get('category', '')
    
    query = "SELECT Artist, song, category, Album, play_cnt, strftime('%Y-%m-%d', last_play_dt) AS last_play_dt, strftime('%Y-%m-%d', date_added) AS date_added FROM tracks WHERE 1=1"
    if q_dict['artist']:
        query += " AND lower(Artist) LIKE '%" + q_dict['artist'].lower() + "%'"
    if q_dict['song']:
        query += " AND lower(song) LIKE '%" + q_dict['song'].lower() +  "%'"
    if q_dict['category']:
        query += " AND category LIKE '%" + q_dict['category'].lower() + "%'"
    
    q_dict['query'] = query
    q_dict['order_by_cols'] = ['artist', 'song']
    q_dict['per_page'] = per_page
    q_dict['page'] = page    
    
    tracks, count = query_table(**q_dict)
    total_pages = (count + per_page - 1) // per_page     
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)  
    template_name= 'tracks.html'
    endpoint='ktunes.tracks'
    return render_template('table_templ.html', template_name=template_name, endpoint=endpoint, tracks=tracks, count=count, total_pages=total_pages, page=page, per_page=per_page, start_page=start_page, end_page=end_page, q_dict=q_dict, background_image_url=background_image_url)

@ktunes.route('/del_playlist', methods=['GET', 'POST'])
def del_playlist():
    if request.method == 'POST':
        selected_playlists = request.form.getlist('selected_playlists')
        if selected_playlists:
            db = get_db_connection()
            for playlist_name in selected_playlists:
                # Delete rows from Playlist
                delete_playlist_query = "DELETE FROM Playlist WHERE playlist_nm = ?"
                db.execute(delete_playlist_query, (playlist_name,))
                # Delete related rows from Playlist_tracks
                delete_tracks_query = "DELETE FROM playlist_tracks WHERE playlist_nm = ?"
                db.execute(delete_tracks_query, (playlist_name,))
            db.commit()
            db.close()

    q_dict = {}
    screen_height = request.args.get('screen_height', type=int)
    if screen_height:
        print("got a screen_height of", screen_height)
        max_rows_response = requests.get(f"{request.url_root}get_max_rows?screen_height={screen_height}")
        if max_rows_response.status_code == 200:
            max_rows = max_rows_response.json().get('max_rows')
            per_page = max_rows
        else:
            per_page = 20
    else:
        print("didn't get a screen height")
        per_page = request.args.get('per_page', 20, type=int)

    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    q_dict['playlist'] = request.args.get('playlist', 'kTunes')

    # Query the 'Playlist' table instead of 'playlist_tracks'
    query = "SELECT playlist_nm, playlist_dt, nbr_of_songs FROM Playlist WHERE lower(playlist_nm) like '" + q_dict['playlist'].lower() + "%'"

    q_dict['query'] = query
    q_dict['order_by_cols'] = ['playlist_nm']  # You can change the order as needed
    q_dict['per_page'] = per_page
    q_dict['page'] = page

    tracks, count = query_table(**q_dict)
    total_pages = (count + per_page - 1) // per_page
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)
    endpoint = 'del_playlist'
    template_name = 'del_playlist.html'

    return render_template('table_templ.html', template_name=template_name, endpoint=endpoint, tracks=tracks,
                           count=count, total_pages=total_pages, page=page, per_page=per_page,
                           start_page=start_page, end_page=end_page, q_dict=q_dict)

# Register the blueprint
app.register_blueprint(ktunes)

if __name__ == "__main__":
   # load the xml file into the database
   if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        config.read(config_path)
        itunes_lib_file = config['misc']['itunes_lib']
        load_xml.main(itunes_lib_file)
   # run the this flask app
   app.run(debug=True)
