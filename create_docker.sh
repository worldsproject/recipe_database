docker kill web_db
sleep 1
docker rm web_db
sleep 1
docker kill recipe_database
sleep 1
docker rm recipe_database
sleep 1
docker run -d -v /web_db --name web_db -p 5432:5432 library/postgres
echo "docker run -d -t --name recipe_database -p 80:80 --link web_db:web_db recipe_database"
#wait 10
#docker inspect -f '{{ .NetworkSettings.IPAddress }}' recipe_database
