echo "Removing app.db"
rm app.db
echo "Removing Search DB Folder."
rm -r search.db/
echo "Recreating DB"
pwd | echo
echo "bob"
python ./db_create.py
