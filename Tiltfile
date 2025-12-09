print(
    """
-----------------------------------------------------------------
✨ Hello Tilt! This appears in the (Tiltfile) pane whenever Tilt
   evaluates this file.
-----------------------------------------------------------------
""".strip()
)

load("ext://syncback", "syncback")

docker_build(
    "backend",
    context="backend",
    build_args={"DEVEL": "yes", "TEST": "yes"},
    live_update=[
        sync("./backend/config", "/app/src/config"),
        sync("./backend/bsbingo", "/app/src/bsbingo"),
    ],
)



k8s_yaml(
    kustomize("./k8s/local/")
)

syncback(
    "backend-sync",
    "deploy/backend",
    "/app/src/bsbingo/",
    target_dir="./backend/bsbingo",
    rsync_path='/app/bin/rsync.tilt',
)




k8s_resource(workload='backend', port_forwards=8000)
k8s_resource(workload='mailhog', port_forwards=8025)
k8s_resource(workload='postgres', port_forwards=5432)

