## Prerequisites

- Kubernetes 1.16+
- Helm 3+

## Install Chart
### Kube
```console
$ kubectl create namespace monitoring
```

### Helm
```console
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 
$ helm repo update
$ helm search repo prometheus-community
$ helm install [RELEASE_NAME] prometheus-community/kube-prometheus-stack -n monitoring
```

### Check its status by running:
```console
$ kubectl get pods -n monitoring
``` 

### Get access to Grafana or Prometeuse panel:

```console
If you have a Kube cluster on vBox and you want to get access to the grafana or prometeuse panel from your PC, you need to Сhange ClusterIP to NodePort:

$ kubectl patch svc [YOUR_SERVICE_NAME] --type='json' -p '[{"op":"replace","path":"/spec/type","value":"NodePort"},{"op":"replace","path":"/spec/ports/0/nodePort","value":30040}]'

For the reverse scenario of converting from NodePort to ClusterIP

$ kubectl patch svc [YOUR_SERVICE_NAME] --type='json' -p '[{"op":"replace","path":"/spec/type","value":"ClusterIP"},{"op":"replace","path":"/spec/ports/0/nodePort","value":null}]'
```

## Uninstall Chart
```console
$ helm list
$ helm uninstall [RELEASE_NAME]
```
CRDs created by this chart are not removed by default and should be manually cleaned up:
```console
kubectl delete crd alertmanagerconfigs.monitoring.coreos.com
kubectl delete crd alertmanagers.monitoring.coreos.com
kubectl delete crd podmonitors.monitoring.coreos.com
kubectl delete crd probes.monitoring.coreos.com
kubectl delete crd prometheuses.monitoring.coreos.com
kubectl delete crd prometheusrules.monitoring.coreos.com
kubectl delete crd servicemonitors.monitoring.coreos.com
kubectl delete crd thanosrulers.monitoring.coreos.com
```

Webhook
```console
kubectl get validatingwebhookconfiguration -All
kubectl delete validatingwebhookconfiguration/kube-prometheus-stack-admission -All

kubectl get mutatingwebhookconfiguration -A
kubectl delete mutatingwebhookconfiguration/kube-prometheus-stack-admission -A
```

## References
   - [prometheus-community](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack>)
   - [Setup Prometheus Monitoring on Kubernetes using Helm and Prometheus Operator](https://www.youtube.com/watch?v=QoDqxm7ybLc)
   - [Мониторинг с Prometheus в Kubernetes за 15 минут](https://habr.com/ru/company/flant/blog/340728/)
   - [Kubernetes NodePort vs LoadBalancer vs Ingress? Когда и что использовать?](https://habr.com/ru/company/southbridge/blog/358824/)

