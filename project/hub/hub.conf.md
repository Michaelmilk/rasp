# About hub.conf

```
{
    # IP address of Gateway device
    "gateway_addr": "localhost",
    
    # Port of Gateway device
    "gateway_port": 6001,
    
    # Host of Hub device
    "hub_host": "0.0.0.0",
    
    # Port of Hub device
    "hub_port": 6000,
    
    # List of local sensors' config
    "sensors":[
        {
            # Type of sensor. Driver of sensor should be "sensor_stub.py" if type is "stub"
            "type": "stub",
            
            # Unique ID of sensor
            "id": "stub001",
            
            # Desciption of sensor
            "desc": "test sensor 1",
            
            # Time interval between two sampling on sensor, in seconds
            "interval": 7.5
        },
        # Add more sensors!
        {
            "type":"stub",
            "id": "stub002",
            "desc": "test sensor 2",
            "interval": 10.0
        }
    ]
}
```