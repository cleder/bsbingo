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
    context=".",
    dockerfile="./backend/Dockerfile",
    build_args={"DEVEL": "yes", "TEST": "yes"},
    live_update=[
        sync("./backend/config", "/app/src/config"),
        sync("./backend/bingo", "/app/src/bingo"),
        # Compiled TS output (`cd frontend && npm run build`), served via
        # STATICFILES_DIRS at /app/frontend/dist (see backend/Dockerfile's
        # frontend-build stage, which bakes this in for a from-scratch
        # image build too).
        sync("./frontend/dist", "/app/frontend/dist"),
    ],
)



k8s_yaml(
    kustomize("./k8s/local/")
)

syncback(
    "backend-sync",
    "deploy/backend",
    "/app/src/bingo/",
    target_dir="./backend/bingo",
    rsync_path='/app/bin/rsync.tilt',
)




k8s_resource(workload='backend', port_forwards=[8000, 5678])
k8s_resource(workload='mailhog', port_forwards=8025)
k8s_resource(workload='postgres', port_forwards=5432)
