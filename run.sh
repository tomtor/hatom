HA=/tmp/ha
mkdir $HA $HA/tmp
docker run -p 41234:41234/udp -v $HA:/home/tom hatom
