WITH expanded AS (
 SELECT evaluation_year,'S0' AS strategy,y,keep_S0 AS keep FROM loan_marks
 UNION ALL SELECT evaluation_year,'S1',y,keep_S1 FROM loan_marks
 UNION ALL SELECT evaluation_year,'S2',y,keep_S2 FROM loan_marks
), counts AS (
 SELECT evaluation_year,strategy,COUNT(*) AS N,SUM(y) AS B,SUM(keep) AS K,
 SUM(keep*y) AS B_keep,SUM((1-keep)*y) AS B_remove,SUM((1-keep)*(1-y)) AS G_remove
 FROM expanded GROUP BY evaluation_year,strategy
)
SELECT *,1.0*K/N AS actual_retained_ratio,1.0*B_keep/NULLIF(K,0) AS retained_chargeoff_ratio,
 1.0*B_remove/NULLIF(B,0) AS chargeoff_capture_rate,
 1.0*G_remove/NULLIF(N-B,0) AS paid_exclusion_rate
FROM counts ORDER BY evaluation_year,strategy;
