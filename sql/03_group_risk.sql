-- 三年×90个冻结组完整网格；空组风险为NULL，权重为0。
WITH counts AS (
 SELECT m.year,m.group_id,COUNT(*) AS n,SUM(l.y) AS b
 FROM membership m JOIN labels l ON l.year=m.year AND l.loan_id=m.loan_id
 GROUP BY m.year,m.group_id
), totals AS (SELECT year,COUNT(*) AS N FROM labels GROUP BY year)
SELECT t.year,g.group_id,g.purpose_group,g.fico_band,
 COALESCE(c.n,0) AS loan_count,COALESCE(c.b,0) AS charged_off_count,
 COALESCE(c.n,0)-COALESCE(c.b,0) AS fully_paid_count,t.N AS population_count,
 1.0*COALESCE(c.n,0)/t.N AS population_share,
 1.0*c.b/NULLIF(c.n,0) AS chargeoff_ratio,
 CASE WHEN COALESCE(c.n,0)<300 OR COALESCE(c.b,0)<20 OR COALESCE(c.n-c.b,0)<20 THEN 1 ELSE 0 END AS risk_estimate_unstable
FROM totals t CROSS JOIN groups g LEFT JOIN counts c ON c.year=t.year AND c.group_id=g.group_id
ORDER BY t.year,g.group_order;
