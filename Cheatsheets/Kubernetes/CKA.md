```kubectl top pod --no-headers | head -n 1 | cut -d " " -f 1```


Find all nodes that DON'T have NoSchedule taint?

```kubectl get node -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.taints[*].effect}{"\n"}{end}' | grep -v NoSchedule```

```kubectl get node -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.taints[*].effect}{"\n"}{end}' | grep -i -v noSchedule |```


```kubectl run busybox --image=busybox --restart=Never --rm -it -- env > envpod.yaml```
