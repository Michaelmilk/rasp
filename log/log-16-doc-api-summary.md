# Doc: API Summary

[TOC]

## Modules

1. Client
2. DataServer(port 8053)
3. Gateway(port 8052)
4. Hub(port 8051)
5. Sensor

## Client

TDB

## DataServer

### API - Accept from Client:

#### `GET dataserver/notify`

> HTTP 1.1 keep-alive for pushing sensor data and events.
> Response: 200 json, data and events

#### `GET dataserver/project`

> Get current project info.
> Response: 200 json, project info. TODO

- - -

#### `POST dataserver/dataserverconfig/(dataserver_id)`

> Configure a device.
> Payload is a json string containing proper config.
> Response: 200 json

#### `POST dataserver/gatewayconfig/(dataserver_id)/(gateway_id)`

> Configure a device.
> Payload is a json string containing proper config.
> Response: 200 json

#### `POST dataserver/hubconfig/(dataserver_id)/(gateway_id)/(hub_id)`

> Configure a device.
> Payload is a json string containing proper config.
> Response: 200 json

- - -

#### `GET dataserver/dataserverconfig/(dataserver_id)`

#### `GET dataserver/gatewayconfig/(dataserver_id)/(gateway_id)`

#### `GET dataserver/hubconfig/(dataserver_id)/(gateway_id)/(hub_id)`

### API - Accept from Gateway

#### `POST dataserver/sensordata`

> Push data to DataServer from Gateway.
> Response: 200 empty

### API - Send to Gateway

#### `POST gateway/gatewayconfig/(gateway_id)`

> Configure a device.
> POST payload is a json string containing proper config.
> Response: 200 json, new config of that device.

#### `POST gateway/hubconfig/(gateway_id)/(hub_id)`

> Configure a device.
> POST payload is a json string containing proper config.
> Response: 200 json, new config of that device.

```
# To Gateway:

    # Configure a device.
    # POST payload is a json string containing proper config.
    # Response: 200 json
    #           New config of that device.
    POST gateway/gatewayconfig/(gateway_id)
    POST gateway/hubconfig/(gateway_id)/(hub_id)

    # Get config of a device.
    # Response: 200 json
    #           Current config of that device.
    GET  gateway/gatewayconfig/(gateway_id)
    GET  gateway/hubconfig/(gateway_id)/(hub_id)
```

### Config

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

## Gateway

### API - Accept from DataServer

#### `POST gateway/gatewayconfig/(gateway_id)`

> Configure a device.
> POST payload is a json string containing proper config.
> Response: 200 json, new config of that device.

**LOCK** self.gateway

#### `POST gateway/hubconfig/(gateway_id)/(hub_id)`

> Configure a device.
> POST payload is a json string containing proper config.
> Response: 200 json, new config of that device.

**LOCK** self.gateway

#### `GET gateway/gatewayconfig/(gateway_id)`

> Get config of a device.
> Response: 200 json, current config of that device.

**LOCK** self.gateway

#### `GET gateway/hubconfig/(gateway_id)/(hub_id)`

> Get config of a device.
> Response: 200 json, current config of that device.

**LOCK** self.gateway

### API - Accept from Hub

#### `POST gateway/sensordata`

> Push data to DataServer from Gateway.
> Response: 200 empty

### API - Send to DataServer

#### `POST dataserver/sensordata`

> Push sensor data.
> Response: 200 empty

### API - Send to Hub

#### `GET hub/hubconfig/(hub_id)`

> Get config of a device.
> Response: 200 json, current config of that device.

Called in processing `GET gateway/hubconfig/(gateway_id)/(hub_id)`

#### `POST hub/hubconfig/(hub_id)`

> Configure a device.
> POST payload is a json string containing proper config.
> Response: 200 json, new config of that device.

Called in processing `POST gateway/hubconfig/(gateway_id)/(hub_id)`

### Config

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

## Hub

```
Members

HubServer
    hub
    bottle
```

### API - Accept from Gateway

#### `POST hub/hubconfig/(hub_id)`

> Configure a device.
> POST payload is a json string containing proper config.
> Response: 200 json, new config of that device.
> Error:    500 json

**LOCK** self.hub

#### `GET  hub/hubconfig/(hub_id)`

> Get config of a device.
> Response: 200 json, current config of that device.
> Error:    500 json

**LOCK** self.hub

### API - Send to Gateway

#### `POST gateway/sensordata`

> Push sensor data.
> Response: 200 empty

### Config

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
            "type": str,
            "id": str,
            "desc": str,
            "interval": float,
            "config": {
                ...
            }
        },
        ...
    ]
}
```
