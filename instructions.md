# Running

python -m shiny run gui_ml_upc.py  
python -m shiny run --reload gui_ml_upc.py (to see code changes immediately)

CMD  
docker compose up -d  
docker exec -it aldimi_mysql_container mysqladmin -u root -paldimi_super_secret ping  
type init.sql | docker exec -i aldimi_mysql_container mysql -u root -paldimi_super_secret aldimi_db  
show tables;  
Comprobar: docker exec -it aldimi_mysql_container mysql -u root -paldimi_super_secret aldimi_db  
SHOW TABLES;  
CTRL + d



"Family_History",
"Radiation_Exposure",
"Iodine_Deficiency",
"Smoking",
"Obesity",
"Diabetes",
"Thyroid_Cancer_Risk"