WITH counts AS (
 SELECT evaluation_year,candidate,reference,group_id,COUNT(*) AS loan_count,
 SUM(CASE WHEN exchange_group='swap_in' THEN 1 ELSE 0 END) AS swap_in_count,
 SUM(CASE WHEN exchange_group='swap_out' THEN 1 ELSE 0 END) AS swap_out_count,
 SUM(CASE WHEN exchange_group='swap_in' THEN y ELSE 0 END) AS swap_in_bad,
 SUM(CASE WHEN exchange_group='swap_out' THEN y ELSE 0 END) AS swap_out_bad
 FROM loan_pairs GROUP BY evaluation_year,candidate,reference,group_id
), sizes AS (SELECT evaluation_year,SUM(keep_S0) AS K FROM loan_marks GROUP BY evaluation_year)
SELECT t.evaluation_year,p.candidate,p.reference,g.group_id,g.purpose_group,g.fico_band,
 COALESCE(c.loan_count,0) AS loan_count,COALESCE(c.swap_in_count,0) AS swap_in_count,COALESCE(c.swap_out_count,0) AS swap_out_count,
 COALESCE(c.swap_in_bad,0) AS swap_in_bad,COALESCE(c.swap_out_bad,0) AS swap_out_bad,
 COALESCE(c.swap_in_bad,0)-COALESCE(c.swap_out_bad,0) AS retained_bad_difference,
 100.0*(COALESCE(c.swap_in_bad,0)-COALESCE(c.swap_out_bad,0))/NULLIF(t.K,0) AS contribution_pp
FROM sizes t CROSS JOIN strategy_pairs p CROSS JOIN groups g
LEFT JOIN counts c ON c.evaluation_year=t.evaluation_year AND c.candidate=p.candidate AND c.reference=p.reference AND c.group_id=g.group_id
ORDER BY t.evaluation_year,p.candidate,p.reference,g.group_order;
