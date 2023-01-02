.header on
.mode column
select a.genre, max(artist_cnt) artist_cnt, genre_cnt, genre_cnt/max(artist_cnt) repeat
from 
(
select  genre, artist, count(*) artist_cnt	
  from tracks
 where genre in ('RecentAdd', 'Latest', 'In Rot', 'Other', 'Old', 'Album')
group by genre, artist
) a,
(select genre, count(*) genre_cnt
   from tracks
group by genre
) b
where a.genre=b.genre
group by a.genre
