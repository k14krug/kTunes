from flask import Flask, render_template, request, Blueprint, redirect, url_for
from flask import jsonify
from flask import flash
from flask import session
from flask_login import login_required, current_user
from login import login_manager, login_blueprint # my login.py module
import configparser
import sqlite3
import random
import os
import psutil # to insure nginx is running
from pathlib import Path
import subprocess
import shutil
import process_db as process_db
import load_xml
from validate_playlist import validate_playlist

# # #
#
# App requires nginx to be running to allow it to listen on port 5000 for any app running on 
# Other ports (like this app running on app 5001) to be redirected to 5000
# 
# # #
app = Flask(__name__)
app.secret_key = 'ktunes secret key #8Ghj^&*'
app.register_blueprint(login_blueprint)  # register the blueprint

login_manager.init_app(app)
login_manager.login_view = "login.login"  # set the login_view

# Define the blueprint
ktune = Blueprint('ktunes', __name__, url_prefix='/ktunesv1.1')

# Database
DATABASE = 'kTunes.sqlite'


class QueryDict:
    def __init__(self):
        self.q_dict = {
            'artist': '',
            'artist_common_name': '',
            'common_name_used': '',
            'song': '',
            'category': '',
            'playlist': '',
            'per_page': 20,
            'query': '',
            'order_by_cols': [],
            'page': 1,
            # Add any other keys you need here
        }


    def get_int_arg(self, key, default):
        value = request.form.get(key, request.args.get(key))
        return int(value) if value and value.isdigit() else default
    
    def get_args_from_page_or_session(self):
        self.q_dict['artist']             = request.args.get('artist', session.get('artist', ''))
        self.q_dict['artist_common_name'] = request.args.get('artist_common_name', session.get('artist_common_name', ''))
        self.q_dict['common_name_used']   = request.args.get('common_name_used', session.get('common_name_used', ''))
        self.q_dict['song']               = request.args.get('song', session.get('song', ''))
        self.q_dict['category']           = request.args.get('category', session.get('category', ''))
        self.q_dict['playlist']           = request.args.get('playlist', session.get('playlist', ''))
        self.q_dict['per_page']           = self.get_int_arg('per_page', 20)
        self.q_dict['page']           = int(request.args.get('page', 1))
        self.q_dict['sort']               = request.args.get('sort')
        self.q_dict['sort_direction']     = request.args.get('direction', session.get('direction', 'asc'))      

        # Store the retrieved values in the session
        session['playlist']           = self.q_dict['playlist']
        session['artist_common_name'] = self.q_dict['artist_common_name']
        session['common_name_used']   = self.q_dict['common_name_used']
        session['artist']             = self.q_dict['artist']
        session['song']               = self.q_dict['song']
        session['category']           = self.q_dict['category']
        session['per_page']           = self.q_dict['per_page']
        session['sort']               = self.q_dict['sort']
        session['sort_direction']     = self.q_dict['sort_direction']
        
    def calc_page_vals(self, count):
        self.q_dict['total_pages'] = (count + self.q_dict['per_page'] - 1) // self.q_dict['per_page']
        self.q_dict['start_page']  = max(1, self.q_dict['page'] - 2)
        self.q_dict['end_page']    = min(self.q_dict['total_pages'], self.q_dict['page']+ 2)
        

QD = QueryDict()

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
            "playlist_type"
            "itunes_xml_file": 'iTunesMusicLibrary.xml',
            "debug_lvl": ""
        },
        "category.Latest": {
            "pct":'30',
            "artist_repeat": '21',
            "ra_playcnt": '14',
            "wild_card": 'Latest%%'
        }
    }
    print("before reading default_config")
    config.read_dict(default_config)
    with open(config_path, "w") as config_file:
        config.write(config_file)
    

# Select a random background image from the list
#selected_image = random.choice(background_images)

# Generate the URL for the selected image
#background_image_url = f"/static/images/{selected_image}"

playlist_cat_cnt = [0,0,0,0,0,0]

# Function to query a table with filters and paginate the result set
def query_table():
    conn = get_db_connection()
    db = conn.cursor()
    count_query = f"SELECT count(*) FROM ({QD.q_dict['query']})"
    cursor = db.execute(count_query)
    count = cursor.fetchone()[0]
    offset = (QD.q_dict['page'] - 1) * QD.q_dict['per_page']
    limit = QD.q_dict['per_page']
    order_by_str = ', '.join(QD.q_dict['order_by_cols'])
    direction = QD.q_dict['sort_direction']
    query = f"{QD.q_dict['query']} ORDER BY {order_by_str} {direction} LIMIT ?, ?"
    #print("query=",query)
    cursor = db.execute(query, (offset, limit))
    tracks = cursor.fetchall()
    cursor.close()
    QD.calc_page_vals(count)
    return tracks, count

@ktune.route('/about')
@login_required
def about():
    return render_template('about.html')

@ktune.route('/settings', methods=['GET', 'POST'])
@login_required
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
        
        try:
            # Get a list of files in the directory
            file_list = os.listdir(linux_directory_path)
        except OSError:
            pass
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
                    load_xml_dict = {}
                    load_xml_dict = load_xml_file()
                    print("load_xml_dict=",load_xml_dict)
                    if load_xml_dict['status'] == 'success':
                        message = f'"{itunes_lib_file}" was copied to {load_xml_dict["xml_file"]}.<br> File date: {load_xml_dict["last_modified_date"]}<br>{load_xml_dict["song_count_inserts"]} songs inserted into the database.'
                    else:
                        message = f'Error: {load_xml_dict["message"]}'
                else:
                    message = f'Choose the itunes library file from {directory_path}'
    return render_template('settings.html', config=config, message=message, file_list=file_list)

# route to create a new playlist
@ktune.route("/cr_playlist", methods=["GET", "POST"])
@login_required
def create_playlist():
    print(current_user.id)  # This will print the username of the logged-in user
    username=current_user.id
    # Read the configuration file
    config.read(config_path)

    error_msg = ""
    success_msg = ""
    copy_msg = ""
    categories = []
    wild_card = []
    playlist_cat_cnt = []
    lib_cat_cnt = []
    category_repeat_interval = []
    total_songs = 0
    if request.method == "POST":  
        #form_data = request.form
        # Retreive the form fields for the misc section of the configuration file
        config["misc"]["playlist_name"] = request.form["playlist_name"]
        config["misc"]["playlist_lgth"] = request.form["playlist_lgth"]
        config["misc"]["playlist_type"] = request.form["playlist_type"]

        total_pct = 0
        category_names = []
        # artist_repeat value is the number of songs before an artist can repeat in a category (roughly)
        artist_repeat_values = []

        # Update category data with form data
        for i in range(len(request.form.getlist('name[]'))):
            category_dict = {
                'name': request.form.getlist('name[]')[i],
                'wild_card': request.form.getlist('wild_card[]')[i] if i < len(request.form.getlist('wild_card[]')) else '',
                'ra_playcnt': request.form.getlist('ra_playcnt[]')[i] if i < len(request.form.getlist('ra_playcnt[]')) else '',
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
            config.set(section_name, 'ra_playcnt', category_dict["ra_playcnt"])

        if total_pct != 100:
           error_msg = "# # # Category 'Percent' column must total 100 (current total is {}). Category configurations not saved. # # #.".format(total_pct)
        else:  
            # Write out the config file
            with open(config_path, "w") as config_file:
                config.write(config_file)
            
            submission_method = request.form.get("submissionMethod")
            print("submission_method=",submission_method)
            if submission_method == "CreatePlaylist":
                # call process_db
                total_songs, playlist_cat_cnt, lib_cat_cnt, dup_playlist, failed_selection_list = process_db.main(usrname=username, cat_dict_list=categories, misc=config['misc'],create_playlst=True)
                
                # Validate generated playlist
                validation_errors, validation_error_msgs = validate_playlist(username, config['misc']['playlist_name'],category_names,artist_repeat_values)
                #print("validation_errors",validation_errors)
                if validation_errors > 0:
                    error_msg = validation_error_msgs
                    #error_msg = "# # # Playlist created but has {} validation error(s). # # #.".format(validation_errors)
                else:
                    
                   
                    success_msg = "Playlist created successfully with {} songs. ".format(total_songs)
                    #  iterate through failed_selection_list. If any have a value > then zero Add it to the success_msg.
                    #  The addition message should inlcude the category name as found in the dictionary for this iteration.
                    #  The additional msg should only print if there is a failed selection
                    for i in range(len(failed_selection_list)):
                        if failed_selection_list[i] > 0:
                            success_msg += "Category {} failed to select {} song(s). ".format(category_names[i], failed_selection_list[i])
                    


            elif submission_method == "UploadPlaylist":
                itunes_dir = config['misc']['itunes_dir']

                # Convert the Windows path to a WSL path
                itunes_dir_wsl = "/mnt/c/" + itunes_dir.replace("C:\\", "").replace("\\", "/")

                # Construct the source file path and destination directory
                src_file = Path.cwd() / (config["misc"]["playlist_name"] + ".m3u")
                dest_dir = Path(itunes_dir_wsl)
 
                # Run unix2dos on the file
                subprocess.run(["unix2dos", str(src_file)], capture_output=True, text=True)

                # Copy the file
                subprocess.run(["cp",  str(src_file), str(dest_dir)], capture_output=True, text=True)
                copy_msg = "{} copied to iTunes directory {}. ".format(config["misc"]["playlist_name"] + ".m3u", itunes_dir)

                # Run the VBScript with the playlist file as an argument
                vbscript_path = str(Path(itunes_dir) / "ImportM3U.vbs")
                playlist_path = str(Path(itunes_dir) / (config["misc"]["playlist_name"] + ".m3u"))
                playlist_path_windows = playlist_path.replace("/", "\\")

                print("vbscript_path=",vbscript_path,"playlist_path=",playlist_path_windows)
                vbscript_result = subprocess.run(["cmd.exe", "/c", "cscript", vbscript_path, playlist_path_windows], capture_output=True, text=True)
                

                print("vbs output:", vbscript_result.stdout)
                print("vbs error:", vbscript_result.stderr)
            else:
                total_songs, playlist_cat_cnt, lib_cat_cnt, dup_playlist = process_db.main(usrname=username, cat_dict_list=categories, misc=config['misc'], create_playlst=False)
                
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
                    'ra_playcnt': config.get(section, 'ra_playcnt', fallback='')
                }
                categories.append(category_dict)
    # Create a list of category names
    category_names = [category['name'] for category in categories]

    # Convert the list to a format suitable for SQL IN clause
    category_names_str = ', '.join(f"'{name}'" for name in category_names)

    stmnt = f'''
    SELECT COUNT(DISTINCT artist_common_name) AS artist_count, category
    FROM tracks
    WHERE category IN ({category_names_str})
    GROUP BY category
    '''
    conn = get_db_connection()
    sql_stmnt = conn.cursor()
    sql_stmnt.execute(stmnt)
    rows=sql_stmnt.fetchall()
    distinct_artists = [None] * len(categories)
    # Add the distinct artist count to the category dictionaries
    for row in rows:
        # Find the corresponding category dictionary
        for i, category in enumerate(categories):
            if category['name'] == row['category']:
                # Add the new key/value pair
                category['dist_artist_cnt'] = row['artist_count']
                # Add the count to the list at the corresponding index
                distinct_artists[i] = row['artist_count']
                break
        
    return render_template("cr_playlist.html", endpoint='ktunes.playlist', categories=categories, config=config, total_songs=total_songs, track_counts_list=playlist_cat_cnt, tot_songs=lib_cat_cnt, distinct_artists=distinct_artists, repeat_interval=category_repeat_interval, error_msgs=error_msg, success=success_msg, copy=copy_msg)

# Route to display the paginated table of a playlist
@ktune.route('/playlist', methods=['GET', 'POST'])
@login_required
def playlist():
    tab_name='ktunes playlist'
    username=current_user.id
  
    # Get the artist, song, and category parameters from the request or the session
    # If there is no value in the request, use the value from the session
    QD.get_args_from_page_or_session()
   
    query = f"""
        SELECT playlist_nm, track_cnt,
            CASE 
                WHEN artist != artist_common_name THEN artist_common_name || '[' || artist || ']'
                ELSE artist
            END as artist,
            song, category, play_cnt, strftime('%Y-%m-%d', last_play_dt) AS last_play_dt 
        FROM playlist_tracks 
        WHERE username = '{username}'
          AND lower(playlist_nm) like '{QD.q_dict['playlist'].lower()}%'
    """
    if QD.q_dict['artist']:
        query += f" AND (lower(artist_common_name) LIKE '%{QD.q_dict['artist'].lower()}%' OR lower(artist) LIKE '%{QD.q_dict['artist'].lower()}%')"
    if QD.q_dict['song']:
        query += f" AND lower(song) LIKE '%{QD.q_dict['song'].lower()}%'"
    if QD.q_dict['category']:
        query += f" AND category LIKE '%{QD.q_dict['category'].lower()}%'"
    
    QD.q_dict['query'] = query

    # Check if the user submitted the sorting form
    if request.method == 'GET' and 'sort' in request.args:
        sort = request.args['sort']
        #print("sorting request.args['sort']=",request.args['sort'])
    else:
        # Use the default sort order if the form is not submitted
        #print(" Not sorting request.method=",request.method,"request.args=",request.args)
        sort = 'track_cnt'
    
    QD.q_dict['order_by_cols'] = [sort]
    
    tracks, count = query_table()
    endpoint = 'ktunes.playlist' 
    template_name= 'playlist.html'
    columns = ['playlist_nm', 'track_cnt', 'artist', 'song', 'category', 'play_cnt', 'last_play_dt']
    return render_template('table_templ.html', tab_name=tab_name, template_name=template_name, endpoint=endpoint, columns=columns, tracks=tracks, count=count, q_dict=QD.q_dict, sort=sort)


# Route to update the track's ktunes_last_play_dt and ktunes_play_cnt
@ktune.route('/update_last_play_dt', methods=['GET', 'POST'])
@login_required
def update_last_play_dt():
    tab_name='ktunes update'
    playlist_nm = request.args.get('playlist_nm')
    track_cnt = request.args.get('track_cnt')

    QD.get_args_from_page_or_session()
        
    query = f"""
        select pt.playlist_nm, pt.track_cnt, t.artist, t.song, 
        substr(datetime(strftime('%Y-%m-%d %H:%M', t.last_play_dt), '-07:00'), 1, 16) as last_play_dt, 
        substr(datetime(strftime('%Y-%m-%d %H:%M', t.ktunes_last_play_dt), '-07:00'), 1, 16) as ktunes_last_play_dt, 
        t.play_cnt, t.ktunes_play_cnt
        from tracks t,
            playlist_tracks pt
        where pt.playlist_nm = '{playlist_nm}'
        and pt.artist = t.artist
        and pt.song= t.song
        and pt.track_cnt < 600
        """
    
    QD.q_dict['query'] = query    
    
    # Check if the user submitted the sorting form
    if request.method == 'GET' and 'sort' in request.args:
        sort = request.args['sort']
        #print("sorting request.args['sort']=",request.args['sort'])
    else:
        # Use the default sort order if the form is not submitted
        #print(" Not sorting request.method=",request.method,"request.args=",request.args)
        sort = 'pt.track_cnt'
  
    QD.q_dict['order_by_cols'] = [sort]
    
    tracks, count = query_table()
    template_name= 'update_last_play_dt.html'
    endpoint='ktunes.update_last_play_dt'
    return render_template('table_templ.html', tab_name=tab_name, playlist_nm=playlist_nm, template_name=template_name, endpoint=endpoint, tracks=tracks, count=count, total_pages=QD.q_dict['total_pages'], q_dict=QD.q_dict, sort=sort)

# Print out all routes
@ktune.after_request
def print_routes(response):
    print(app.url_map)
    return response

# Route to display the paginated table of tracks
@ktune.route('/tracks', methods=['GET', 'POST'])
@login_required
def tracks(artist=None):
    try:
        page = int(request.args.get('page', 1))
        print("page=",page)
    except ValueError:
        print("ValueError")
        page = 1

    
    print("Start of tracks. per_page=",request.form.get('per_page', type=int))
    
    QD.get_args_from_page_or_session()
    # If the function was passed a value for artist use it and also ignore values for song and category
    if artist is not None:
        QD.q_dict['artist'] = artist
        QD.q_dict['song'] = ''
        QD.q_dict['category'] = ''
    
    query = f"""SELECT 
                    CASE 
                        WHEN t.artist != t.artist_common_name THEN t.artist_common_name || '[' || t.artist || ']'
                        ELSE t.artist
                    END as artist,
                    t.song song,
                    CASE 
                        WHEN pt.category IS NOT NULL THEN t.category || '(' || pt.category || ')'
                        ELSE t.category
                    END as category,
                    album, t.play_cnt, strftime('%Y-%m-%d', t.last_play_dt) AS last_play_dt, 
                    strftime('%Y-%m-%d', date_added) AS date_added,
                    ktunes_genre as genre, strftime('%Y-%m-%d',ktunes_last_play_dt) as ktunes_last_play_dt, ktunes_play_cnt 
                FROM tracks t 
                LEFT JOIN (select distinct song, artist, category, max(playlist_dt) 
                            from playlist_tracks 
                            where category = 'RecentAdd'
                            group by song, artist) pt ON 
                        t.artist = pt.artist 
                    AND t.song = pt.song
                where 1=1"""
    
    if QD.q_dict['artist']:
        query += f" AND (lower(t.artist_common_name) LIKE '%{QD.q_dict['artist'].lower()}%' OR lower(t.artist) LIKE '%{QD.q_dict['artist'].lower()}%')"
    if QD.q_dict['song']:
        query += f" AND lower(t.song) LIKE '%{QD.q_dict['song'].lower()}%'"
    if QD.q_dict['category']:
        query += f" AND t.category LIKE '%{QD.q_dict['category'].lower()}%'"

    QD.q_dict['query'] = query    
    
    # Check if the user submitted the sorting form
    if request.method == 'GET' and 'sort' in request.args:
        sort = request.args['sort']
        #print("sorting request.args['sort']=",request.args['sort'])
    else:
        # Use the default sort order if the form is not submitted
        #print(" Not sorting request.method=",request.method,"request.args=",request.args)
        sort = 'artist'
  
    QD.q_dict['order_by_cols'] = [sort]
    
    #print("QD.q_dict['query']=",QD.q_dict['query'],"QD.q_dict['order_by_cols']=",QD.q_dict['order_by_cols'],"QD.q_dict['per_page']=",QD.q_dict['per_page'],"QD.q_dict['page']=",QD.q_dict['page'])
    tracks, count = query_table()
    template_name= 'tracks.html'
    endpoint='ktunes.tracks'
    columns = ['artist', 'song', 'category', 'album', 'play_cnt', 'last_play_dt', 'date_added', 'ktunes_last_play_dt', 'ktunes_play_cnt', 'genre']
            
    return render_template('table_templ.html', template_name=template_name, endpoint=endpoint, columns=columns, tracks=tracks, count=count, total_pages=QD.q_dict['total_pages'],  q_dict=QD.q_dict,  sort=sort)

def update_artist_common_name(artist, common_name):
    conn = get_db_connection()
    db = conn.cursor()
    update_query = "UPDATE tracks SET artist_common_name = ? WHERE artist = ?"
    print("update_artist_common_name artist=",artist,"common_name=",common_name, "update_query",update_query)
    db.execute(update_query, (common_name, artist))
    db.commit()
    db.close()

@ktune.route('/ktunes_artist', methods=['GET', 'POST'])
@login_required
def ktunes_artist():
    
    

    # Get the artist, song, and category parameters from the request or the session
    if request.method == 'POST':
        per_page = request.form.get('per_page', 20, type=int)
        QD.q_dict['artist'] = request.form.get('artist', session.get('artist', ''))
        QD.q_dict['artist_common_name'] = request.form.get('artist_common_name', session.get('artist_common_name', ''))
        QD.q_dict['common_name_used'] = request.form.get('common_name_used', session.get('common_name_used', ''))
        common_names = {k[12:]: v for k, v in request.form.items() if k.startswith('common_name_')}
        original_common_names = {k[21:]: v for k, v in request.form.items() if k.startswith('original_common_name_')}
        print("In post of ktunes_artist, common_names=",common_names,"original_common_names=",original_common_names)
        for artist, common_name in common_names.items():
            original_common_name = original_common_names.get(artist)
            print("  In loop, artist=",artist,"common_name=",common_name,"original_common_name=",original_common_name)
            if common_name != original_common_name:
               update_artist_common_name(artist, common_name)
               print("updating artist tracks",artist,"with common name",common_name)
        # Redirect to the same page to prevent form resubmission
        return redirect(url_for('ktunes.ktunes_artist', artist=QD.q_dict['artist']))
    else:
        QD.get_args_from_page_or_session()

    
    if QD.q_dict['common_name_used']:
        # The following shows which artist have their artist_common_name set to another artist. They should be considered as that artist.
        # But its possible that the artist_common_name was entered wrong and doesn't have a match to any artist in the artist column.
        # In this case the record will have 'Data Error' appended to the artist name. You will have to manually fix these records.
        query = '''
            SELECT 
                CASE 
                    WHEN NOT EXISTS (SELECT 1 FROM tracks WHERE artist = combined.artist_common_name) THEN combined.artist || ' - Data Error?'
                    ELSE combined.artist
                END as artist,
                COUNT(*) as track_count, 
                combined.artist_common_name
            FROM (
                SELECT artist, artist_common_name FROM tracks WHERE artist != artist_common_name
                UNION ALL
                SELECT artist, artist AS artist_common_name FROM tracks
                WHERE artist IN (
                    SELECT artist_common_name FROM tracks WHERE artist != artist_common_name
                )
            ) AS combined
            where 1=1
            '''
    else:
        query = '''
            SELECT artist, COUNT(*) track_count, artist_common_name 
            FROM tracks 
            where 1=1
        '''
    if QD.q_dict['artist']:
        query += " AND lower(Artist) LIKE '%" + QD.q_dict['artist'].lower() + "%'"

    if QD.q_dict['artist_common_name']:
        query += " AND lower(Artist_common_name) LIKE '%" + QD.q_dict['artist_common_name'].lower() + "%'"

    

    query += " GROUP BY artist"
    
    QD.q_dict['query'] = query

    QD.q_dict['order_by_cols'] = ['artist_common_name']

    sort='artist'

    tracks, count = query_table()
    template_name= 'ktunes_artist.html'
    endpoint='ktunes.ktunes_artist'
    return render_template('table_templ.html', template_name=template_name, endpoint=endpoint, tracks=tracks, count=count, total_pages=QD.q_dict['total_pages'],  q_dict=QD.q_dict,  sort=sort)

    #return render_template('artist_tracks.html', template_name=template_name, endpoint=endpoint, tracks=tracks,)

@ktune.route('/list_playlist', methods=['GET', 'POST'])
@login_required
def list_playlist():
    username=current_user.id
   
    # Get the playlist parameter from the request or the session
    QD.get_args_from_page_or_session(   )
    if request.method == 'POST':
        QD.q_dict['playlist'] = request.form.get('playlist', session.get('playlist', ''))
    
    # Store the playlist parm in the session
    session['playlist'] = QD.q_dict['playlist']
    
    if request.method == 'POST':
        selected_playlists = request.form.getlist('selected_playlists')
        if selected_playlists:
            for playlist_name in selected_playlists:    
                pass
            conn.close()

    
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    # Query the 'Playlist' table instead of 'playlist_tracks'
    query = "SELECT playlist_nm, playlist_dt, nbr_of_songs FROM Playlist WHERE username = '" + username + "' and lower(playlist_nm) like '" + QD.q_dict['playlist'].lower() + "%'"

    QD.q_dict['query'] = query
    QD.q_dict['order_by_cols'] = ['playlist_nm']  # You can change the order as needed
    
    tracks, count = query_table()
    endpoint = 'ktunes.list_playlist'
    template_name = 'list_playlist.html'

    return render_template('table_templ.html', template_name=template_name, endpoint=endpoint, tracks=tracks, count=count,  q_dict=QD.q_dict)


@ktune.route('/del_playlist', methods=['GET', 'POST'])
@login_required
def del_playlist():
    username=current_user.id
   
    # Get the playlist parameter from the request or the session
    QD.get_args_from_page_or_session(   )
    if request.method == 'POST':
        QD.q_dict['playlist'] = request.form.get('playlist', session.get('playlist', ''))
    
    # Store the playlist parm in the session
    session['playlist'] = QD.q_dict['playlist']
    
    if request.method == 'POST':
        selected_playlists = request.form.getlist('selected_playlists')
        if selected_playlists:
            conn = get_db_connection()
            db = conn.cursor()
            for playlist_name in selected_playlists:    
                # Delete rows from Playlist
                delete_playlist_query = "DELETE FROM Playlist WHERE username = ? and playlist_nm = ?"
                db.execute(delete_playlist_query, (username, playlist_name,))
                # Delete related rows from Playlist_tracks
                delete_tracks_query = "DELETE FROM playlist_tracks WHERE username = ? and playlist_nm = ?"
                db.execute(delete_tracks_query, (username, playlist_name,))
            conn.commit()
            conn.close()

    
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    # Query the 'Playlist' table instead of 'playlist_tracks'
    query = "SELECT playlist_nm, playlist_dt, nbr_of_songs FROM Playlist WHERE username = '" + username + "' and lower(playlist_nm) like '" + QD.q_dict['playlist'].lower() + "%'"

    QD.q_dict['query'] = query
    QD.q_dict['order_by_cols'] = ['playlist_nm']  # You can change the order as needed
    
    tracks, count = query_table()
    endpoint = 'ktunes.del_playlist'
    template_name = 'del_playlist.html'

    return render_template('table_templ.html', template_name=template_name, endpoint=endpoint, tracks=tracks, count=count,  q_dict=QD.q_dict)

# Register the blueprints
app.register_blueprint(ktune)

def is_nginx_running():
    for process in psutil.process_iter(['pid', 'name']):
        if 'nginx' in process.info['name']:
            return True
    return False

def load_xml_file():
    config.read(config_path)
    itunes_lib_file = config['misc']['itunes_lib']
    load_xml_dict=load_xml.main(itunes_lib_file)
    return(load_xml_dict)

if __name__ == "__main__":
    if is_nginx_running():
        # load the xml file into the database only when truly starting, not on debug restart.
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            load_xml_file()
            # run the this flask app
        #app.run(host='your_local_ip', port=5000)
        #print(app.url_map)
        print("starting the app")
        #print(app.url_map)
        app.run(debug=True,port=5000)
        
    else:
        print('Nginx is not running. Please start Nginx before running this Flask app.')

