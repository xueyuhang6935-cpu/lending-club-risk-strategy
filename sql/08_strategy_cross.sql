WITH counts AS (
 SELECT evaluation_year,candidate,reference,exchange_group AS "group",COUNT(*) AS loan_count,SUM(y) AS charged_off_count
 FROM loan_pairs GROUP BY evaluation_year,candidate,reference,exchange_group
), kinds("group") AS (VALUES('common_remove'),('swap_in'),('swap_out'),('common_keep')),
 totals AS (SELECT evaluation_year,COUNT(*) AS N FROM loan_marks GROUP BY evaluation_year)
SELECT t.evaluation_year,p.candidate,p.reference,k."group",
 COALESCE(c.loan_count,0) AS loan_count,COALESCE(c.charged_off_count,0) AS charged_off_count,
 COALESCE(c.loan_count,0)-COALESCE(c.charged_off_count,0) AS fully_paid_count,
 1.0*COALESCE(c.loan_count,0)/t.N AS population_share,
 1.0*c.charged_off_count/NULLIF(c.loan_count,0) AS chargeoff_ratio
FROM totals t CROSS JOIN strategy_pairs p CROSS JOIN kinds k
LEFT JOIN counts c ON c.evaluation_year=t.evaluation_year AND c.candidate=p.candidate AND c.reference=p.reference AND c."group"=k."group"
ORDER BY t.evaluation_year,p.candidate,p.reference,k."group";
