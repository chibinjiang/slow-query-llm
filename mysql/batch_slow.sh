for i in $(seq 1 200); do
  mysql -uroot -p${PWD} -D employees -e "
    SELECT e.emp_no, e.first_name, e.last_name, s.salary
    FROM employees e
    JOIN salaries s ON e.emp_no = s.emp_no
    WHERE YEAR(s.from_date) = 1985;
  " >/dev/null
done