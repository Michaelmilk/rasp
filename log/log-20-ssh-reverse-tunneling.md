# 关于SSH反向代理

先认为有两台主机，位于外网的A和位于内网的B。

```
[B]    |            [A]
```

在B用ssh访问A，请求建立ssh隧道：

`ssh -R [A映射端口]:[A映射主机]:[B目标端口] [A用户名]@[A地址]`

如

`ssh -R 20000:localhost:8080 tgmerge@100.100.100.100`

其后A访问自身的20000端口，即相当于访问B的8080端口。

```
            |
[B]         |             [A]
8080 <------+---------- 20000
            |
```

流程相关。

```
                       | [Forwarder]
                       | 1. Start sshd
                       | 2. Provide /forwarder/regserver
                       | 
                       |
                       |
```

对RegXXX的流程改进。

```
For node:
  1. send server/regnode 'Introduce'
  2. send server/keepnode/<node_id> 'Do you know me?'
     - Get 'yes': loop
     - Get 'no' : send server/regnode 'Introduce'

For server:
  1. Get server/regnode:
       add node to known list
       refresh node's "last active" timestamp
  2. Get server/keepnode/<node_id>
       find node in known list
       - if found: reply 'yes'
       - not found: reply 'no'

```