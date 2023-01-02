.header on
.mode column
select song, artist, last_play_dt, last_played, rating, length, repeat_cnt, location
                            from tracks
                          where genre = 'Latest'
                            and last_played <= 9999 
                            order by last_play_dt
