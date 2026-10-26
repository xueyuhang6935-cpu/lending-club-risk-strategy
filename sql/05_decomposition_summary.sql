WITH sums AS (
 SELECT comparison,previous_year,later_year,MAX(total_count_0) AS N_0,MAX(total_count_1) AS N_1,
 SUM(b_0) AS B_0,SUM(b_1) AS B_1,
 SUM(S_g) AS S,SUM(I_g) AS I,SUM(A_g) AS A,SUM(T_g) AS total_T,
 SUM(CASE WHEN support_status='new_in_later' THEN 1 ELSE 0 END) AS new_group_count,
 SUM(CASE WHEN n_1>0 THEN w_1*r_0 ELSE 0.0 END) AS known_counterfactual
 FROM group_contributions GROUP BY comparison,previous_year,later_year
)
SELECT *,1.0*B_1/N_1-1.0*B_0/N_0 AS delta_R,
 CASE WHEN new_group_count=0 THEN known_counterfactual ELSE NULL END AS R_cf,
 CASE WHEN new_group_count=0 THEN 1 ELSE 0 END AS R_cf_estimable,
 (1.0*B_1/N_1-1.0*B_0/N_0)-(S+I+A) AS residual,
 100*S AS S_pp,100*I AS I_pp,100*A AS A_pp
FROM sums ORDER BY previous_year;
