# 关于反向代理，forwarder之类

1. 浏览器/绘图库
2. 反向代理
3. demo -> 继续
4. 模块结构图

Web      HTTP
bottle - gevent
bottle - nginx

```
  chart.html            |
  how_to_draw_chart.js  |
->[server1]80           |
             \          |
              \         |
               \        |reverse proxy
                --------|------------->8080[forwarder][80]<----------- M
               /        |
              /         |
             /          |
->[server2]80           |
  how_to_draw_chart.js  |
  chart.html            |
```