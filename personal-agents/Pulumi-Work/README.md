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
