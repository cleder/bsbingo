# Bootstrap k3s and ArgoCD

After deploying infrastructure using Terraform, we can proceed with configuring
k3s and bootstrapping ArgoCD.

Terraform is solely utilized for deploying infrastructure. Any subsequent
configuration of k3s or ArgoCD is done using Taskfile tasks.

To view a list of tasks and their descriptions, navigate to the
`bootstrap-cluster` directory and execute `task`.

Note that there is a directory for each environment: sandbox, staging, and
cluster.

We recommend opening the AWS serial console for each ec2 instance to monitor the
bootstrap process.

### Bootstrapping k3s

1. Navigate to the directory corresponding to the environment being set up and
   run:

   ```shell
   export ENV=sandbox
   cd $ENV
   ```

2. Review the `.env` file for the given environment:

   ```shell
   CONTROL_PLANE_ENDPOINT: "https://k8s.sandbox.example.test:6443"
   CLUSTER_NAME: "bsbingo-sandbox"
   ```
3. Bootstrap k3s with the following command:

   ```
   task k3s:bootstrap
   ```

   To understand what this task will do, examine the Taskfile configuration:

   ```yaml
   bootstrap:
     desc: |
       Run all tasks required to bootstrap k3s and Kubernetes cluster.
     requires:
       vars: [ENV]
     cmds:
       - task: save-node-ips
       - task: setup-ssh-key
       - task: install-k3s
       - task: fetch-kubeconfig
       - task: store-kubeconfig
       - task: enable-ecr-credential-helper
   ```

   It takes a few minutes for the cluster nodes to register as etcd
   members and synchronize.

   If the cluster fails to bootstrap, refer to the Troubleshooting section
   below.

4. Test kubectl access:

   ```shell
   eval $(task k3s:kubeconfig)
   kubectl cluster-info
   ```

   This should return output similar to the following:

   ```shell
   $ kubectl cluster-info
   Kubernetes control plane is running at https://k8s.sandbox.example.test:6443
   CoreDNS is running at https://k8s.sandbox.example.test:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

   To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
   ```

### Bootstrapping ArgoCD

1. Review the branches used for deployment to the sandbox, staging and
   production environments. The default configuration will release the `develop`
   branch to the Sandbox and the `main` branch to the Production environment.
   Make sure to make the `develop` branch the default branch for PRs on a newly
   created Git repository.

   Review the branch rule in `bootstrap_root_app` job in
   `bootstrap-cluster/argocd.yaml`:

   ```
   vars:
     BRANCH:
       sh: ([ "$ENV" = "production" ] && echo "main" || echo "develop")
   ```

   Review the `targetRevision` in the `kustomization.yaml` files shown below:

   `argocd/sandbox/apps/kustomization.yaml`:

   ```
   patches:
   - patch: |-
       - op: replace
         path: /spec/source/targetRevision
         value: develop
     target:
       kind: Application
       name: ingress
   ...
   - patch: |-
       - op: replace
         path: /spec/source/targetRevision
         value: develop
     target:
       kind: Application
       name: bsbingo-prod
   ```

   `argocd/prod/apps/kustomization.yaml`:

   ```
   patches:
   - patch: |-
       - op: replace
         path: /spec/source/targetRevision
         value: main
     target:
       kind: Application
       name: ingress
   ```

2. Next, we need to create a GitHub deploy key to allow ArgoCD to monitor the
   repo. This step requires access to the 1password vault for your project.

   Review the vault name in the `op` cli command in
   `bootstrap-cluster/argocd.yaml`:

   ```
      - op item create
          ...
          --vault='BsBingo'
   ```

   Sign into 1password with `op signin` and generate the deploy key:

   ```shell
   task argocd:generate_github_deploy_key
   ```

3. Add the deploy key to your Git repository

4. Proceed with installing ArgoCD by executing:

   ```shell
   task argocd:bootstrap
   ```

The `argocd:bootstrap` task configuration is as follows:

```
  bootstrap:
      desc: Setup ArgoCD
      cmds:
        - task: install
        - task: create_repo_credentials_secret
        - task: bootstrap_root_app
```

5. ArgoCD will install the Sealed Secrets operator in the cluster. Once it is
   installed, we can generate secrets for the given environment.

   ```shell
   cd ..
   make debug-$ENV-secrets
   make $ENV-secrets
   ```

6. Commit the `secrets.yaml` file for the given environment and push it to the
   repo.

## Troubleshooting
If bootstrapping k3s fails, we recommend uninstalling k3s from each node and
boostrapping from scratch.

```shell
task k3s:uninstall-k3s
```
