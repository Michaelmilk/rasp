# Doc: API Summary

[TOC]

## Modules

Client, DataServer, Gateway, Hub, Sensor

### Client

### DataServer

#### API - Accept

```
# From Client:
    
    # HTTP 1.1 keep-alive for pushing sensor data and events.
    # Response: 200 json
    #           Data and events
    GET  dataserver/notify
    
    # Configure a device.
    # POST payload is a json string containing proper config.
    # Response: 200 json
    #           New config of that device.
    POST dataserver/dataserverconfig/(dataserver_id)
    POST dataserver/gatewayconfig/(gateway_id)
    POST dataserver/hubconfig/(hub_id)
    
    # Get config of a device.
    # Response: 200 json
    #           Current config of that device.
    GET  dataserver/dataserverconfig/(dataserver_id)
    GET  dataserver/gatewayconfig/(gateway_id)
    GET  dataserver/hubconfig/(hub_id)

    # Get current project info.
    # Response: 200 json
    #           Project info. TODO
    GET  dataserver/project

# From Gateway

    # Push data to DataServer from Gateway.
    # Response: 200 empty
    POST dataserver/sensordata
```

#### API - Send

```
# To Gateway:

    # Configure a device.
    # POST payload is a json string containing proper config.
    # Response: 200 json
    #           New config of that device.
    POST gateway/gatewayconfig/(gateway_id)
    POST gateway/hubconfig/(hub_id)

    # Get config of a device.
    # Response: 200 json
    #           Current config of that device.
    GET  gateway/gatewayconfig/(gateway_id)
    GET  gateway/hubconfig/(hub_id)
```

#### Config

```
DataServerConfig:

{
    "dataserver_id": str,
    "dataserver_desc": str,
    "dataserver_host": str,
    "dataserver_port": int,
    "gateways": [
        {
            "gateway_id": str,
            "gateway_desc": str,
            "gateway_addr": str,
            "gateway_port": int,
        },
        ...
    ]
}
```

### Gateway

#### API - Accept

```
# From DataServer:
    
    # Configure a device.
    # POST payload is a json string containing proper config.
    # Response: 200 json
    #           New config of that device.
    POST gateway/gatewayconfig/(gateway_id)
    POST gateway/hubconfig/(hub_id)
    
    # Get config of a device.
    # Response: 200 json
    #           Current config of that device.
    GET  gateway/gatewayconfig/(gateway_id)
    GET  gateway/hubconfig/(hub_id)

# From Hub

    # Push data to DataServer from Gateway.
    # Response: 200 empty
    POST gateway/sensordata
```

#### API - Send

```
# To DataServer:

    # Push sensor data.
    # Response: 200 empty
    POST dataserver/sensordata

# To Hub:

    # Configure a device.
    # POST payload is a json string containing proper config.
    # Response: 200 json
    #           New config of that device.
    POST hub/hubconfig/(hub_id)

    # Get config of a device.
    # Response: 200 json
    #           Current config of that device.
    GET  hub/hubconfig/(hub_id)
```

#### Config

```
GatewayConfig:

{
    "gateway_id": str,
    "gateway_desc": str,
    "gateway_host": str,
    "gateway_port": int,
    "dataserver_host": str,
    "dataserver_port": int,
    "hubs": [
        {
            "hub_id": str,
            "hub_desc": str,
            "hub_addr": str,
            "hub_port": int,
        },
        ...
    ],
    "filters": [
        {
            "apply_on_sensor_type": str / "*" for any type / "" for none
            "apply_on_sensor_id": str / "*" for any id / "" for none
            "comparing_method": "greater_than" / "less_than"
            "threshold": float
        },
        ...
    ]
}
```

### Hub

#### API - Accept

```
# From Gateway:
    
    # Configure a device.
    # POST payload is a json string containing proper config.
    # Response: 200 json
    #           New config of that device.
    POST hub/hubconfig/(hub_id)
    
    # Get config of a device.
    # Response: 200 json
    #           Current config of that device.
    GET  hub/hubconfig/(hub_id)
```

#### API - Send

```
# To Gateway:

    # Push sensor data.
    # Response: 200 empty
    POST gateway/sensordata
```

#### Config

```
HubConfig:

{
    "hub_id": str,
    "hub_desc": str,
    "hub_host": str,
    "hub_port": int,
    "gateway_host": str,
    "gateway_port": int,
    "sensors": [
        {
            "sensor_type": str,
            "sensor_id": str,
            "sensor_desc": str,
            "sensor_config": {
                ...
            }
        },
        ...
    ]
}
```
