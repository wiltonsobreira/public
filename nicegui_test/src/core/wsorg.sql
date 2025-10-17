-- BACKUP TABLE
ALTER TABLE bookmark RENAME TO bookmark_bkp_01;

-- DROP TABLE
DROP TABLE bookmark;

-- CREATE TABLE
CREATE TABLE bookmark (
	nm_bookmark VARCHAR NOT NULL,
	ds_bookmark VARCHAR,
	nm_grouping VARCHAR,
	nm_group_bookmark VARCHAR, 
	nm_subgroup_bookmark VARCHAR,
	nm_tag VARCHAR,
	url_bookmark VARCHAR NOT NULL,
	ts_created DATETIME DEFAULT CURRENT_TIMESTAMP, 
	ts_updated DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (nm_bookmark)
);

CREATE INDEX ix_bookmark_nm_grouping ON bookmark (nm_grouping);
CREATE INDEX ix_bookmark_nm_group_bookmark ON bookmark (nm_group_bookmark);
CREATE INDEX ix_bookmark_nm_subgroup_bookmark ON bookmark (nm_subgroup_bookmark);
CREATE INDEX ix_bookmark_nm_tag ON bookmark (nm_tag);

-- INSERT BY BACKUP
INSERT INTO bookmark
(
  nm_bookmark
, ds_bookmark
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
, NULL as nm_grouping
, gp_bookmark as nm_group_bookmark
, sbgp_bookmark as nm_subgroup_bookmark
, NULL as nm_tag
, url_bookmark
, ts_created
, ts_updated
FROM bookmark_bkp_01;