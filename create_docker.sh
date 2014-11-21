docker kill web_db
wait 10
docker rm web_db
wait 10
docker kill recipe_database
wait 10
docker rm recipe_database
wait 10
docker run -d -v /web_db --name web_db library/postgres
wait 10
echo "docker run -d -t --name recipe_database --link web_db:web_db recipe_database"
#wait 10
#docker inspect -f '{{ .NetworkSettings.IPAddress }}' recipe_database