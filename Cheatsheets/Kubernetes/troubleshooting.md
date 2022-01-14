#### error: listen tcp 127.0.0.1:8001: bind: address already in use
Get the process:
```sh
$ ps aux | grep kubectl
```
kill the process:
```sh
$ kill -9 1549
```
kubectl proxy:
```sh
$ kubectl proxy
```
