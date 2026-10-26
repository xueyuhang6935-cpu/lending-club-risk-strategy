-- SQLite 3。输入为已经核查的批次状态聚合，不冒充逐贷款原始状态表。
SELECT approval_year, term, loan_status, SUM(loan_count) AS loan_count
FROM cohort_status
GROUP BY approval_year, term, loan_status
ORDER BY approval_year, term, loan_status;
