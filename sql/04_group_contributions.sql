-- 冻结顺序：先替换结构，后替换组内核销比例。新增支持的S/I未知，不补零。
WITH pairs(previous_year,later_year) AS (VALUES(2014,2015),(2015,2016)), joined AS (
 SELECT p.previous_year||'_to_'||p.later_year AS comparison,p.previous_year,p.later_year,
 a.group_id,a.purpose_group,a.fico_band,
 a.loan_count AS n_0,a.charged_off_count AS b_0,a.population_count AS total_count_0,
 b.loan_count AS n_1,b.charged_off_count AS b_1,b.population_count AS total_count_1,
 a.population_share AS w_0,b.population_share AS w_1,
 a.chargeoff_ratio AS r_0,b.chargeoff_ratio AS r_1,
 CASE WHEN a.loan_count>0 AND b.loan_count>0 THEN 'both_present'
      WHEN a.loan_count=0 AND b.loan_count>0 THEN 'new_in_later'
      WHEN a.loan_count>0 AND b.loan_count=0 THEN 'absent_in_later' ELSE 'empty_both' END AS support_status
 FROM pairs p JOIN group_risk a ON a.year=p.previous_year
 JOIN group_risk b ON b.year=p.later_year AND b.group_id=a.group_id
), components AS (
 SELECT *,
 CASE support_status WHEN 'both_present' THEN (w_1-w_0)*r_0 WHEN 'absent_in_later' THEN -w_0*r_0 WHEN 'empty_both' THEN 0.0 ELSE NULL END AS S_g,
 CASE support_status WHEN 'both_present' THEN w_1*(r_1-r_0) WHEN 'new_in_later' THEN NULL ELSE 0.0 END AS I_g,
 CASE WHEN support_status='new_in_later' THEN w_1*r_1 ELSE 0.0 END AS A_g,
 1.0*b_1/total_count_1-1.0*b_0/total_count_0 AS T_g
 FROM joined
)
SELECT *,100*S_g AS S_g_pp,100*I_g AS I_g_pp,100*A_g AS A_g_pp,100*T_g AS T_g_pp
FROM components ORDER BY previous_year,group_id;
