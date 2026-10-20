------------------------------------------------------------
Structured output notes:

Before putting structure output into place, I was getting back, as expected, plain text similar to this:

1. Misusing `Output` values as plain strings/ints
2. Wrong resource dependency ordering
3. Incorrect Kubernetes API versions/kind names
4. YAML/manifest schema or indentation mistakes
5. Namespace not created first
6. Missing kubeconfig/context configuration
7. RBAC/permission issues
8. Conflicts with existing cluster-managed resources
9. Secret handling mistakes
10. Immutable field update failures

After structured output put into place, using jq:
cat structured_output.txt | jq
{
  "issues": [
    {
      "ranking": 1,
      "description": "Wrong kubeconfig or current context: Pulumi targets the wrong cluster, or the kubeconfig file/context is missing or stale."
    },
    {
      "ranking": 2,
      "description": "Namespace not created or mismatched: Resources are deployed into a namespace that does not exist or differs from the one referenced by dependent objects."
    },
    {
      "ranking": 3,
      "description": "Missing resource dependencies: Kubernetes objects are created in the wrong order, causing failures for Services, Ingresses, Secrets, CRDs, or RBAC resources."
    },
    {
      "ranking": 4,
      "description": "Invalid YAML/manifest translation: Converting YAML to Python objects incorrectly leads to schema mismatches, bad indentation assumptions, or malformed fields."
    },
    {
      "ranking": 5,
      "description": "Name collisions and duplicate resources: Hardcoded names or reused metadata cause conflicts with existing Kubernetes objects or Pulumi stack state."
    },
    {
      "ranking": 6,
      "description": "Incorrect labels/selectors: Deployments, Services, and Ingresses do not match because labels and selectors are inconsistent."
    },
    {
      "ranking": 7,
      "description": "Secrets/config values handled incorrectly: Plaintext secrets, wrong config keys, or misuse of Pulumi secret outputs causes runtime deployment issues."
    },
    {
      "ranking": 8,
      "description": "CRD not installed before custom resources: Custom resources fail because their CustomResourceDefinition is not present or not fully established yet."
    },
    {
      "ranking": 9,
      "description": "Insufficient RBAC permissions: The kube user/service account used by Pulumi lacks permissions to create or manage required resources."
    },
    {
      "ranking": 10,
      "description": "Output/Apply misuse and async issues: Pulumi Outputs are used as plain strings or resolved too early, leading to type errors or invalid resource arguments."
    }
  ]
}
------------------------------------------------------------
MCP server (serper) use.  After putting the MCP server use in place, 
you must go to https://platform.openai.com/logs?api=traces to 
see it was used. Because we used with trace("Top10PulumiErrorsK8s"), 
you'd look at the trace named "Top10PulumiErrorsK8s"
------------------------------------------------------------
Pretty ugly, but asking for the common fixes for each issue:

================================================================
Find the common solution to Incorrect use of Output values (forgetting .apply, passing unresolved Outputs into plain Python logic)., ranked as 1
Solution to Incorrect use of Output values (forgetting .apply, passing unresolved Outputs into plain Python logic).: RunResult:
- Last agent: Agent(name="PulumiCommonErrors", ...)
- Final output (str):
    Common fix: **don’t use `Output` like a normal Python value**.

    - Use **`.apply(...)`** to transform an `Output`
    - Use **`pulumi.Output.all(...)`** when combining multiple Outputs
    - Keep unresolved Outputs **out of plain Python logic** (`if`, string ops, dict keys, loops, function args that expect real values)

    Example:

    ```python
    bucket_name = my_bucket.id.apply(lambda v: f"{v}-suffix")
    ```

    If you need a plain value for non-Pulumi code, do the computation inside `apply`.
    If you’re seeing this in a Kubernetes deployment, it usually means you passed an `Output` into something that expects a real string/object.

    Rule of thumb: **Pulumi resource inputs can accept Outputs; ordinary Python code cannot.**
- 3 new item(s)
- 2 raw response(s)
- 0 input guardrail result(s)
- 0 output guardrail result(s)
(See `RunResult` for more details)
================================================================
Find the common solution to Missing resource dependencies / wrong ordering (resources created before Namespace, CRD, Secret, etc.)., ranked as 2
Solution to Missing resource dependencies / wrong ordering (resources created before Namespace, CRD, Secret, etc.).: RunResult:
- Last agent: Agent(name="PulumiCommonErrors", ...)
- Final output (str):
    Common fix in Pulumi: **declare explicit dependencies** so Kubernetes resources are created in the right order.

    ### Typical solutions
    - **Namespace first**: create the `Namespace`, then pass `metadata.namespace` to all namespaced resources.
    - **Use `depends_on`** for resources that must exist first:
      - `Namespace`
      - `CustomResourceDefinition`
      - `Secret` / `ConfigMap`
      - controller/operator `Deployment` before CRs it manages
    - **Chain outputs**: if a resource needs an ID/name from another resource, reference that output directly.
    - **Avoid parallel creation** when order matters; Pulumi will only infer dependencies from actual property references.

    ### Example
    ```python
    ns = k8s.core.v1.Namespace("app-ns", metadata={"name": "app-ns"})

    secret = k8s.core.v1.Secret(
        "app-secret",
        metadata={"namespace": ns.metadata["name"]},
        string_data={"token": "abc"},
        opts=pulumi.ResourceOptions(depends_on=[ns]),
    )

    deployment = k8s.apps.v1.Deployment(
        "app",
        metadata={"namespace": ns.metadata["name"]},
        spec=...,
        opts=pulumi.ResourceOptions(depends_on=[secret]),
    )
    ```

    ### For CRDs
    If you create a custom resource, ensure the CRD exists first:
    ```python
    crd = k8s.apiextensions.CustomResourceDefinition(...)
    cr = mygroup.v1.MyResource(
        "cr",
        opts=pulumi.ResourceOptions(depends_on=[crd]),
    )
    ```

    ### If using Helm
    - Use `skip_await` / readiness settings carefully.
    - Sometimes install the chart in one stack step, then create dependent resources in a later step, or use `depends_on` on the Helm release.

    ### Rule of thumb
    If Kubernetes complains “resource not found” or “no matches for kind”, it usually means:
    1. missing `depends_on`, or
    2. the dependency is not actually referenced in the resource inputs, so Pulumi doesn’t know about it.

    If you want, I can give you a **Pulumi Python pattern for Namespace + Secret + Deployment + CRD/CR**.
- 1 new item(s)
- 1 raw response(s)
- 0 input guardrail result(s)
- 0 output guardrail result(s)
(See `RunResult` for more details)
=====================================================================

Find the common solution to Namespace mistakes (resource lands in default namespace or namespace not created/assigned)., ranked as 3
Solution to Namespace mistakes (resource lands in default namespace or namespace not created/assigned).: RunResult:
- Last agent: Agent(name="PulumiCommonErrors", ...)
- Final output (str):
    Common Pulumi/Kubernetes namespace fixes:

    - **Set `metadata.namespace` on every namespaced resource**:
      ```python
      kubernetes.core.v1.Service(
          "svc",
          metadata={"namespace": ns.metadata["name"]},
          ...
      )
      ```

    - **Create the Namespace first, then reference it**:
      ```python
      ns = kubernetes.core.v1.Namespace("ns", metadata={"name": "my-ns"})
      ```

    - **Use the same provider with a default namespace** (if you want everything to land there):
      ```python
      prov = kubernetes.Provider("prov", kubeconfig=kubeconfig, namespace="my-ns")
      ```

    - **Avoid relying on implicit/default namespace behavior**:
      If `namespace` is omitted, many resources go to `default`.

    - **Use `opts=ResourceOptions(parent=ns)` only for dependency ordering**:
      `parent` does **not** assign namespace; it just helps structure dependencies.

    - **For YAML/Helm resources, explicitly set namespace in the chart/value files**:
      Otherwise rendered manifests may still target `default`.

    - **Watch for cluster-scoped resources**:
      `Namespace`, `ClusterRole`, `CustomResourceDefinition`, etc. do not use namespaces.

    Most common root cause: **the resource was created without `metadata.namespace`, so Kubernetes defaulted it to `default`.**
- 1 new item(s)
- 1 raw response(s)
- 0 input guardrail result(s)
- 0 output guardrail result(s)
(See `RunResult` for more details)

=====================================================================
Find the common solution to Provider/authentication issues (bad kubeconfig, expired token, wrong cluster context)., ranked as 4
Solution to Provider/authentication issues (bad kubeconfig, expired token, wrong cluster context).: RunResult:
- Last agent: Agent(name="PulumiCommonErrors", ...)
- Final output (str):
    Common fixes for Pulumi Kubernetes provider/auth issues:

    - **Verify kubeconfig is valid**
      - `kubectl config view --raw`
      - `kubectl get ns`
      - If broken, regenerate kubeconfig from your cluster and update `KUBECONFIG`.

    - **Check the current context**
      - `kubectl config current-context`
      - `kubectl config use-context <correct-context>`
      - Pulumi uses the context in the kubeconfig unless you override it.

    - **Refresh expired credentials/tokens**
      - EKS: `aws eks update-kubeconfig --name <cluster> --region <region>`
      - GKE: `gcloud container clusters get-credentials ...`
      - AKS: `az aks get-credentials ...`
      - Re-login to the cloud provider if needed.

    - **Explicitly point Pulumi to the right kubeconfig/context**
      - Set `kubeconfig` in the provider or `KUBECONFIG` env var.
      - Ensure the provider is using the intended cluster:
        ```python
        provider = kubernetes.Provider("k8s", kubeconfig=kubeconfig)
        ```

    - **If using exec-based auth plugins**
      - Make sure the auth command exists and is in PATH.
      - Upgrade to a supported `client-go`/Kubernetes provider version if auth plugin API changed.

    - **Confirm RBAC permissions**
      - Even with valid auth, missing permissions can look like auth failures.
      - Test with `kubectl auth can-i ...`

    - **Clear stale cached credentials**
      - Remove or refresh cloud auth caches if the token is stuck/expired.

    If you want, I can turn this into a Pulumi-specific troubleshooting checklist or map it to EKS/GKE/AKS separately.
- 1 new item(s)
- 1 raw response(s)
- 0 input guardrail result(s)
- 0 output guardrail result(s)
(See `RunResult` for more details)

=====================================================================
Find the common solution to Helm chart ordering issues with CRDs/custom resources (CRD not ready before CR creation)., ranked as 5
Solution to Helm chart ordering issues with CRDs/custom resources (CRD not ready before CR creation).: RunResult:
- Last agent: Agent(name="PulumiCommonErrors", ...)
- Final output (str):
    Common Pulumi/Kubernetes fix: **separate CRDs from custom resources and enforce ordering with dependencies**.

    ### Typical pattern
    1. **Install CRDs first**
       - Apply CRDs as plain Kubernetes manifests or via the chart’s CRD resources if supported.
    2. **Wait for the CRD to be established**
       - Ensure the API server has registered the CRD before creating any custom resources.
    3. **Create custom resources afterward**
       - Add explicit `dependsOn` from custom resources to the CRD resource.

    ### In Pulumi
    - Use `dependsOn` on the CRD installation resource.
    - If using Helm, prefer:
      - a dedicated CRD chart / separate `kubernetes.yaml.ConfigFile`, or
      - Helm chart options that install CRDs separately, then your custom resources in another step.

    ### Example idea
    ```python
    crd = k8s.apiextensions.CustomResourceDefinition(...)
    cr = k8s.apiextensions.CustomResource(
        ...,
        opts=pulumi.ResourceOptions(depends_on=[crd]),
    )
    ```

    ### If using Helm
    - Some charts have `skipCRDRendering` / `installCRDs` / separate CRD subchart options.
    - Best practice is usually:
      - **CRDs in one stack step**
      - **Helm release/custom resources in the next**

    ### Why this works
    The error happens because Kubernetes accepts the CRD object before the API server has fully established the new type. Explicit dependency ordering prevents Pulumi from racing ahead.

    If you want, I can show the **best Pulumi Python pattern for Helm charts with CRDs** (including `Chart` vs `Release` vs raw YAML).
- 1 new item(s)
- 1 raw response(s)
- 0 input guardrail result(s)
- 0 output guardrail result(s)
(See `RunResult` for more details)

=====================================================================
Find the common solution to Mixing Pulumi resource options incorrectly (provider/depends_on handling, especially with dynamic providers/outputs)., ranked as 6

Solution to Mixing Pulumi resource options incorrectly (provider/depends_on handling, especially with dynamic providers/outputs).: RunResult:
- Last agent: Agent(name="PulumiCommonErrors", ...)
- Final output (str):
    Common fix: **don’t mix a child resource’s `parent` with an inherited `provider` when the child is a dynamic resource**.

    Why:
    - `parent` can cause Pulumi to **inherit the parent’s provider**
    - if that parent has a cloud provider (or a provider with `assumeRole`, aliases, etc.), Pulumi may try to run the dynamic resource’s `Check` against the **wrong provider**
    - this commonly shows up as `unrecognized resource type (Check): pulumi-nodejs:dynamic:Resource`

    ### Usual solutions
    1. **Pass the dynamic provider explicitly**
       - don’t rely on inherited provider behavior
       - set `provider: myDynamicProvider` on the dynamic resource

    2. **Avoid `parent` on the dynamic resource** if it isn’t required
       - this is the documented workaround for the classic bug/edge case

    3. If you need ordering only, use **`dependsOn`**, not `parent`
       - `dependsOn` is the correct option for sequencing
       - Pulumi already tracks dependencies from `Output` inputs automatically

    ### Rule of thumb
    - **`parent`** = ownership / hierarchy / inheritance
    - **`provider`** = which provider executes CRUD
    - **`dependsOn`** = ordering only

    For dynamic providers, keep those concerns separate.
- 9 new item(s)
- 3 raw response(s)
- 0 input guardrail result(s)
- 0 output guardrail result(s)
(See `RunResult` for more details)

=====================================================================
Find the common solution to API version / kind mismatches (using deprecated or wrong Kubernetes API versions)., ranked as 7
Solution to API version / kind mismatches (using deprecated or wrong Kubernetes API versions).: RunResult:
- Last agent: Agent(name="PulumiCommonErrors", ...)
- Final output (str):
    Use the API version that matches your Kubernetes cluster version and resource kind.

    Common fixes:
    - Replace deprecated APIs with the current ones:
      - `extensions/v1beta1` Ingress → `networking.k8s.io/v1`
      - `apps/v1beta1` / `apps/v1beta2` Deployments → `apps/v1`
      - `policy/v1beta1` PodDisruptionBudget → `policy/v1`
      - `rbac.authorization.k8s.io/v1beta1` → `rbac.authorization.k8s.io/v1`
    - Verify the `kind` is correct for the resource.
    - Check what your cluster supports:
      - `kubectl api-versions`
      - `kubectl explain <kind>`
    - If using Pulumi, update the resource type/apiVersion to the current one in your SDK/manifest.

    Example:
    ```yaml
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    ```

    If you want, I can list the most common deprecated Kubernetes APIs and their replacements.
- 1 new item(s)
- 1 raw response(s)
- 0 input guardrail result(s)
- 0 output guardrail result(s)
(See `RunResult` for more details)

=====================================================================
Find the common solution to Readiness/await behavior problems (deployment hangs, pods not becoming ready, skipAwait/await semantics)., ranked as 8
Solution to Readiness/await behavior problems (deployment hangs, pods not becoming ready, skipAwait/await semantics).: RunResult:
- Last agent: Agent(name="PulumiCommonErrors", ...)
- Final output (str):
    Common Pulumi/Kubernetes fixes for readiness/await hangs:

    - **If a resource is “stuck” waiting for readiness**, check whether Pulumi is waiting on a child resource, not the parent. A bad Pod/Probe/Service can block the whole deployment.
    - **Use `skipAwait: true`** on resources where Kubernetes readiness is unreliable or irrelevant (common for Jobs, CRDs/operators, some controllers).
    - **Use `await: false`** only when you intentionally want Pulumi to stop waiting on that resource; prefer `skipAwait` in modern usage for Kubernetes resources.
    - **Fix the workload readiness itself**:
      - ensure `readinessProbe` is valid and not too strict
      - ensure container actually listens on the expected port/path
      - confirm image pulls and startup time are sufficient
      - check events/logs for crash loops or pending scheduling
    - **For Services/Ingress**, make sure backing Pods are Ready and selectors match labels.
    - **For custom resources**, often the controller doesn’t report readiness in a way Pulumi understands; use `skipAwait`.
    - **For Helm charts**, hangs are often due to chart hooks or resources with no meaningful readiness signal; disable await for those resources or the release if appropriate.
    - **For long-running init/bootstrapping**, increase timeouts rather than disabling await if readiness is expected eventually.

    Quick rule:
    - **Real app should become ready** → fix probes/pod spec.
    - **Kubernetes object has no useful readiness signal** → `skipAwait: true`.

    If you want, I can give you a Pulumi YAML/TypeScript example showing `skipAwait` vs default await behavior.
- 1 new item(s)
- 1 raw response(s)
- 0 input guardrail result(s)
- 0 output guardrail result(s)
(See `RunResult` for more details)
=====================================================================

Find the common solution to Secret/config handling mistakes (ConfigMap vs Secret, leaking sensitive values, wrong serialization)., ranked as 9
Solution to Secret/config handling mistakes (ConfigMap vs Secret, leaking sensitive values, wrong serialization).: RunResult:
- Last agent: Agent(name="PulumiCommonErrors", ...)
- Final output (str):
    Common fixes:

    - Use `ConfigMap` for non-sensitive config, `Secret` for passwords/tokens/keys.
    - Never hardcode secrets in code, YAML, or Pulumi outputs.
    - In Pulumi, store sensitive values with `pulumi.Config().require_secret(...)` or `Config.require_secret_object(...)`.
    - Pass secrets to Kubernetes `Secret` data as base64-encoded bytes/strings as expected by the API.
    - Don’t use `stringData` if your tooling/provider mishandles it; prefer explicit `data` with correct encoding.
    - Mark outputs as secret when they contain sensitive values.
    - Avoid printing/exporting secret values in logs, stack outputs, or previews.
    - Ensure the resource type matches the content:
      - app settings → `ConfigMap`
      - credentials/keys → `Secret`
    - Validate serialization:
      - plain text to `ConfigMap`
      - base64 for `Secret.data`
      - JSON/YAML only when the consumer expects it
    - If using env vars, reference secrets via `valueFrom.secretKeyRef`, not plain `env.value`.

    Typical Pulumi pattern:

    ```python
    cfg = pulumi.Config()
    db_password = cfg.require_secret("dbPassword")

    secret = k8s.core.v1.Secret(
        "db-secret",
        metadata={"name": "db-secret"},
        type="Opaque",
        string_data={
            "password": db_password,
        },
    )
    ```

    If you want, I can also give you a short checklist for debugging “Secret created but app can’t read it” issues.
- 1 new item(s)
- 1 raw response(s)
- 0 input guardrail result(s)
- 0 output guardrail result(s)
(See `RunResult` for more details)

=====================================================================
Find the common solution to Drift/state issues after failed updates (refresh/import/replace problems, resources stuck or orphaned)., ranked as 10
Solution to Drift/state issues after failed updates (refresh/import/replace problems, resources stuck or orphaned).: RunResult:
- Last agent: Agent(name="PulumiCommonErrors", ...)
- Final output (str):
    Common Pulumi/Kubernetes drift/state recovery flow after a failed update:

    1. **Refresh first**
       - `pulumi refresh`
       - Reconciles Pulumi state with what actually exists in the cluster/cloud.
       - Fixes many “stuck”/“already exists”/orphaned state mismatches.

    2. **Inspect what’s wrong**
       - `pulumi preview`
       - `pulumi stack export` (compare state vs reality)
       - Check whether the resource:
         - still exists in cluster but not in state
         - is in state but missing in cluster
         - was renamed/recreated manually

    3. **If state is missing a real resource: import it**
       - Use `pulumi import` or add `opts=ResourceOptions(import_=...)`
       - Best for orphaned resources that already exist and should be managed again.

    4. **If state is wrong/corrupt: replace or remove state**
       - Prefer `replace` when the resource can be recreated safely.
       - If the resource is gone but still in state, `pulumi state delete` (or `pulumi state unprotect` first if needed) can clean up stale entries.

    5. **If update partially failed**
       - Re-run with `pulumi up` after refresh.
       - If necessary, target the specific resource:
         - `pulumi up --target <urn>`
       - Avoid broad manual state edits unless necessary.

    6. **For Kubernetes specifically**
       - Common causes:
         - manual `kubectl apply/delete`
         - controller-created resources
         - immutable field changes causing replacement
         - CRDs/operators reconciling desired state
       - Use:
         - `ignoreChanges` for fields owned by controllers
         - `replaceOnChanges` for immutable drift-prone fields
         - `deleteBeforeReplace` when Kubernetes won’t allow in-place replacement

    ### Rule of thumb
    - **Resource exists, Pulumi doesn’t know it** → **import**
    - **Pulumi knows it, cluster doesn’t** → **refresh** or **state delete**
    - **Field/shape changed and can’t patch** → **replace**
    - **State is inconsistent after failure** → **refresh, then import/delete as needed**

    If you want, I can give you a **step-by-step recovery checklist** or **exact commands for a specific broken resource**.
- 1 new item(s)
- 1 raw response(s)
- 0 input guardrail result(s)
- 0 output guardrail result(s)
(See `RunResult` for more details)

