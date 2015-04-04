# 命名更改

getsenserdata
                         100k           100k
hub           -> gateway   -> forwarder -> monitor
                 (html,js)              -> browser
                 
filter           pull from hub

- - -

hub:
    filter
    API:
        GET /hub/sensordata

gateway:
    configurable
    pull from hub by time interval
    static file
    API:
        GET /

forwarder:
    forward http request




monitor req1 req2

gateway req1 -> hub1 100
        req2 -> hub2 0.0001
        

pi  <--->  gateway

* pi should register itself to gateway once started