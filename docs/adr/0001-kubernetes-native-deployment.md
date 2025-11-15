# 1. Kubernetes-Native Deployment from Day 0

Date: 2025-11-15

## Status

Accepted

## Context

The project requires a deployment strategy that:
- Works locally for development
- Transitions seamlessly to production environments
- Remains cloud provider-agnostic
- Supports microservices architecture
- Handles event-driven workloads (Jobs, persistent services)

Traditional approaches (docker-compose, manual deployment) create friction when moving from local to production environments and require significant rework.

## Decision

Adopt Kubernetes with Helm charts as the deployment foundation from day 0.

**Implementation:**
- Helm charts define all infrastructure (Deployments, Jobs, StatefulSets, Ingress)
- Local development uses minikube or kind
- Same manifests used in all environments (dev, staging, production)
- Values files parameterize environment-specific configs

**Key Resources:**
- Deployments: frontend, API
- Jobs: event consumer (Redis Stream → PostgreSQL)
- StatefulSets: PostgreSQL, Redis (or external services)
- Ingress: with rate limiting annotations

## Consequences

### Positive
- **Zero deployment friction:** Same Helm chart works locally and in production
- **Cloud-agnostic:** Works on any K8s provider (GKE, EKS, AKS, on-prem)
- **Native Job support:** K8s Jobs ideal for event consumers
- **Production-ready patterns:** From day 0 (health checks, resource limits, secrets)
- **Scalability built-in:** Horizontal pod autoscaling available when needed

### Negative
- **Learning curve:** Team needs K8s knowledge
- **Local complexity:** Requires minikube/kind instead of just Docker
- **Overhead for MVP:** More initial setup than docker-compose

### Neutral
- **Tooling requirement:** kubectl, Helm required for all developers
- **Resource usage:** Local K8s cluster uses more memory than docker-compose

## Alternatives Considered

### Docker Compose
- **Pros:** Simple local development, widely understood
- **Rejected:** Requires complete rewrite for production, no Job support, not production-grade

### Cloud-specific tooling (AWS CDK, Terraform)
- **Pros:** Infrastructure as code, multi-cloud with Terraform
- **Rejected:** Provider coupling (CDK), requires K8s anyway for orchestration

### Serverless (AWS Lambda, Cloud Functions)
- **Pros:** Minimal infrastructure management
- **Rejected:** Provider lock-in, doesn't fit microservices model, harder local testing

## References

- [Helm Best Practices](https://helm.sh/docs/chart_best_practices/)
- [Kubernetes Jobs Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- Project requirements: `system_requirements.txt`
