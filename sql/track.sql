.header on
.mode column
select song, artist, last_play_dt, last_played, rating, length, repeat_cnt, location,genre
                            from tracks
                          where artist='Bhi Bhiman'
                            order by last_play_dt
