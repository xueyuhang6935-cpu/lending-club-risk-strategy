-- 旧期两类“不满足信用政策但已终结”状态依原上游口径纳入终结计数。
WITH counts AS (
 SELECT approval_year, term, SUM(loan_count) AS total_count,
 SUM(CASE WHEN loan_status IN ('Fully Paid','Does not meet the credit policy. Status:Fully Paid') THEN loan_count ELSE 0 END) AS fully_paid_count,
 SUM(CASE WHEN loan_status IN ('Charged Off','Does not meet the credit policy. Status:Charged Off') THEN loan_count ELSE 0 END) AS charged_off_count
 FROM cohort_status GROUP BY approval_year, term
)
SELECT *, fully_paid_count+charged_off_count AS terminal_count,
 total_count-fully_paid_count-charged_off_count AS nonterminal_count,
 1.0*(fully_paid_count+charged_off_count)/NULLIF(total_count,0) AS terminal_share,
 0 AS snapshot_confirmed, 0 AS contractual_observation_confirmed
FROM counts ORDER BY approval_year, term;
