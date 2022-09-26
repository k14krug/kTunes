select artist, max(last_play_dt) last_play_dt,  count(*) cnt from tracks group by artist;
