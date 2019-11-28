SELECT DISTINCT photoID FROM photo WHERE photoPoster in (
	SELECT username_followed FROM follow WHERE username_follower="Isiah" AND followstatus=1
	)
OR photoID in (
	SELECT photoID FROM sharedwith NATURAL JOIN belongto WHERE member_username="Isiah"
	)