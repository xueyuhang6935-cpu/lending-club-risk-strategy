-- 读取已有冻结决策；不在SQL中重训或重算模型分数。
SELECT l.year AS evaluation_year,l.loan_id,l.source_row,l.issue_month,l.y,
 m.group_id,m.purpose_group,m.fico_band,d.window,
 d.model_version_S0,d.model_version_S1,d.model_version_S2,
 d.keep_S0,d.keep_S1,d.keep_S2,
 CASE 2*d.keep_S0+d.keep_S1 WHEN 0 THEN 'common_remove' WHEN 1 THEN 'swap_in' WHEN 2 THEN 'swap_out' ELSE 'common_keep' END AS exchange_S1_S0,
 CASE 2*d.keep_S0+d.keep_S2 WHEN 0 THEN 'common_remove' WHEN 1 THEN 'swap_in' WHEN 2 THEN 'swap_out' ELSE 'common_keep' END AS exchange_S2_S0,
 CASE 2*d.keep_S1+d.keep_S2 WHEN 0 THEN 'common_remove' WHEN 1 THEN 'swap_in' WHEN 2 THEN 'swap_out' ELSE 'common_keep' END AS exchange_S2_S1
FROM labels l JOIN membership m ON m.year=l.year AND m.loan_id=l.loan_id
JOIN decisions d ON d.year=l.year AND d.loan_id=l.loan_id
ORDER BY l.year,l.source_row;
