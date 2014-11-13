echo "Removing app.db"
rm app.db
echo "Removing Search DB Folder."
rm -r search.db/
echo "Recreating DB"
python db_create.py
