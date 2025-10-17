-- BACKUP TABLE
DROP TABLE bookmark_bkp_01;

ALTER TABLE bookmark RENAME TO bookmark_bkp_01;

-- DROP TABLE
DROP TABLE bookmark;

-- CREATE TABLE tm_bookmark
CREATE TABLE tm_bookmark (
	nm_bookmark VARCHAR NOT NULL,
	ds_bookmark VARCHAR,
	nm_type_bookmark VARCHAR NOT NULL,
	nm_subtype_bookmark VARCHAR NOT NULL,
	nm_grouping VARCHAR,
	nm_group_bookmark VARCHAR, 
	nm_subgroup_bookmark VARCHAR,
	nm_tag VARCHAR,
	url_bookmark VARCHAR NOT NULL,
	ts_created DATETIME DEFAULT CURRENT_TIMESTAMP, 
	ts_updated DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (nm_bookmark)
);

CREATE INDEX ix_bookmark_nm_type_bookmark ON tm_bookmark (nm_type_bookmark);
CREATE INDEX ix_bookmark_nm_subtype_bookmark ON tm_bookmark (nm_subtype_bookmark);
CREATE INDEX ix_bookmark_nm_grouping ON tm_bookmark (nm_grouping);
CREATE INDEX ix_bookmark_nm_group_bookmark ON tm_bookmark (nm_group_bookmark);
CREATE INDEX ix_bookmark_nm_subgroup_bookmark ON tm_bookmark (nm_subgroup_bookmark);
CREATE INDEX ix_bookmark_nm_tag ON tm_bookmark (nm_tag);

-- TRUNCATE TABLE
DELETE FROM tm_bookmark;

-- INSERT BY BACKUP
INSERT INTO tm_bookmark
(
  nm_bookmark
, ds_bookmark
, nm_type_bookmark
, nm_subtype_bookmark
, nm_grouping
, nm_group_bookmark
, nm_subgroup_bookmark
, nm_tag
, url_bookmark
, ts_created
, ts_updated
)
SELECT
  nm_bookmark
, ds_bookmark
, 'website' as nm_type_bookmark
, 'page' as nm_subtype_bookmark
, nm_grouping
, nm_group_bookmark
, nm_subgroup_bookmark
, nm_tag
, url_bookmark
, ts_created
, ts_updated
FROM bookmark_bkp_01;


-- CREATE TABLE tc_type_bookmark
CREATE TABLE tc_type_bookmark (
	nm_type_bookmark VARCHAR NOT NULL,
	ts_created DATETIME DEFAULT CURRENT_TIMESTAMP, 
	ts_updated DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (nm_type_bookmark)
);

-- INSERT tc_type_bookmark
INSERT INTO tc_type_bookmark
(
  nm_type_bookmark
)
SELECT
  'article' as nm_type_bookmark
UNION
SELECT
  'audio' as nm_type_bookmark
UNION
SELECT
  'git' as nm_type_bookmark
  UNION
SELECT
  'social_media' as nm_type_bookmark
  UNION
SELECT
  'video' as nm_type_bookmark
  UNION
SELECT
  'website' as nm_type_bookmark
  UNION
SELECT
  'file' as nm_type_bookmark


  
-- CREATE TABLE tc_subtype_bookmark
CREATE TABLE tc_subtype_bookmark (
	nm_subtype_bookmark VARCHAR NOT NULL,
	ts_created DATETIME DEFAULT CURRENT_TIMESTAMP, 
	ts_updated DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (nm_subtype_bookmark)
);

-- INSERT tc_subtype_bookmark
INSERT INTO tc_subtype_bookmark
(
  nm_subtype_bookmark
)
SELECT
  'channel' as nm_subtype_bookmark
UNION
SELECT
  'file' as nm_subtype_bookmark
UNION
SELECT
  'playlist' as nm_subtype_bookmark
  UNION
SELECT
  'page' as nm_subtype_bookmark
  UNION
SELECT
  'repository' as nm_subtype_bookmark
  UNION
SELECT
  'post' as nm_subtype_bookmark
  UNION
SELECT
  'profile' as nm_subtype_bookmark
  UNION
SELECT
  'domain' as nm_subtype_bookmark



-- All type of favorites

-- favorites/article
-- favorites/audio/channel
-- favorites/audio/file
-- favorites/audio/playlist
-- favorites/git/page
-- favorites/git/repository
-- favorites/social_media/post
-- favorites/social_media/profile
-- favorites/video/channel
-- favorites/video/file
-- favorites/video/playlist
-- favorites/website/domain
-- favorites/website/page
-- favorites/website/post
-- file (other formats)
