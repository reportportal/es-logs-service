call python test_performance.py --data_folder "C:\Users\Maryia_Ivanina\report_portal\auto-analysis-poc\tmp\mckc-auto" --method "index_logs" --data_size 10000000 --query_num 100 --database_type "postgres"
call python test_performance.py --data_folder "C:\Users\Maryia_Ivanina\report_portal\auto-analysis-poc\tmp\mckc-auto" --method "delete_logs_by_date" --data_size 10000000 --query_num 30 --database_type "postgres"