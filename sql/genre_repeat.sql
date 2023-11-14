.header on
.mode column
select a.category, max(artist_cnt) artist_cnt, genre_cnt, genre_cnt/max(artist_cnt) repeat
from 
(
select  category, artist, count(*) artist_cnt	
  from tracks
 where category in ('RecentAdd', 'Latest', 'In Rot', 'Other ', 'Old', 'Album')
group by category, artist
) a,
(select category, count(*) genre_cnt
   from tracks
group by category
) b
where a.category=b.category
group by a.category


--comment