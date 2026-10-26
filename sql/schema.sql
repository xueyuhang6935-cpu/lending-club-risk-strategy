PRAGMA foreign_keys=ON;
CREATE TABLE cohort_status(approval_year INTEGER NOT NULL,term TEXT NOT NULL,loan_status TEXT NOT NULL,loan_count INTEGER NOT NULL CHECK(loan_count>=0),PRIMARY KEY(approval_year,term,loan_status));
CREATE TABLE groups(group_id TEXT PRIMARY KEY,purpose_group TEXT NOT NULL,fico_band TEXT NOT NULL,group_order INTEGER NOT NULL UNIQUE);
CREATE TABLE labels(year INTEGER NOT NULL CHECK(year BETWEEN 2014 AND 2016),loan_id TEXT NOT NULL,source_row INTEGER NOT NULL,issue_month TEXT NOT NULL,y INTEGER NOT NULL CHECK(y IN(0,1)),PRIMARY KEY(year,loan_id),UNIQUE(loan_id),UNIQUE(source_row));
CREATE TABLE membership(year INTEGER NOT NULL,loan_id TEXT NOT NULL,source_row INTEGER NOT NULL,issue_month TEXT NOT NULL,group_id TEXT NOT NULL REFERENCES groups(group_id),purpose_group TEXT NOT NULL,fico_band TEXT NOT NULL,PRIMARY KEY(year,loan_id),FOREIGN KEY(year,loan_id) REFERENCES labels(year,loan_id));
CREATE TABLE decisions(year INTEGER NOT NULL,loan_id TEXT NOT NULL,source_row INTEGER NOT NULL,issue_month TEXT NOT NULL,y INTEGER NOT NULL CHECK(y IN(0,1)),window TEXT NOT NULL,model_version_S0 TEXT NOT NULL,model_version_S1 TEXT NOT NULL,model_version_S2 TEXT NOT NULL,keep_S0 INTEGER NOT NULL CHECK(keep_S0 IN(0,1)),keep_S1 INTEGER NOT NULL CHECK(keep_S1 IN(0,1)),keep_S2 INTEGER NOT NULL CHECK(keep_S2 IN(0,1)),PRIMARY KEY(year,loan_id),FOREIGN KEY(year,loan_id) REFERENCES labels(year,loan_id));
CREATE TABLE strategy_pairs(candidate TEXT NOT NULL,reference TEXT NOT NULL,PRIMARY KEY(candidate,reference));
INSERT INTO strategy_pairs VALUES('S1','S0'),('S2','S0'),('S2','S1');
CREATE VIEW loan_pairs AS
 SELECT evaluation_year,loan_id,y,group_id,'S1' AS candidate,'S0' AS reference,exchange_S1_S0 AS exchange_group FROM loan_marks
 UNION ALL SELECT evaluation_year,loan_id,y,group_id,'S2','S0',exchange_S2_S0 FROM loan_marks
 UNION ALL SELECT evaluation_year,loan_id,y,group_id,'S2','S1',exchange_S2_S1 FROM loan_marks;
