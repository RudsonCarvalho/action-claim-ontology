[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18930044.svg)](https://doi.org/10.5281/zenodo.18930044)

# Toward an Operational Ontology of Agentic Action

**Author:** Rudson Kiyoshi Souza Carvalho
**Version:** 1.0.0 — 2026-03-09
**License:** [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)

---

## Abstract

As agentic systems move from experimentation into regulated, high-stakes, and multi-agent environments, the core problem is no longer merely orchestration — it is governability. This paper introduces the Action Claim as the correct pre-execution governance object: a contestable, machine-evaluable proposal that a specific world-state transition should be permitted, structured across declared, derived, and delegation-supplied fields. We argue that governing agentic systems requires not just a protocol for transmitting such objects, but an operational ontology — a typed, reusable semantic framework that defines what exists in the domain of agent action, how effects compose, and how governance systems can evaluate them before execution.

---

## Specification

The `spec/` directory contains the formal technical specification of the Action Claim object and its operational ontology. This specification is a companion artifact to the paper, expanding on the formal definitions, schema, and evaluation model introduced in the text.

> **Status:** v0.1 — draft

See [`spec/README.md`](spec/README.md) for an overview of all specification documents.

---

## Repository Structure

```
action-claim-ontology/
├── README.md                    # This file
├── CITATION.cff                 # Machine-readable citation metadata
├── LICENSE                      # CC BY 4.0
├── paper/
│   └── .gitkeep                 # PDF available on Zenodo (see link above)
└── spec/
    ├── README.md                # Specification overview and design principles
    ├── action-claim.md          # Field-by-field specification of the Action Claim object
    ├── ontology.md              # Operational ontology: entities, relations, and scope
    ├── delegation-chain.md      # Delegation chain structure and mandate propagation rules
    ├── evaluation-model.md      # Governance evaluation model and latency tiers
    ├── composition-axioms.md    # Formal axioms for effect composition
    └── schema/
        └── action-claim.json    # JSON Schema (Draft 2020-12)
```

---

## Paper

The full PDF is available on Zenodo:

> [https://doi.org/10.5281/zenodo.18930044](https://doi.org/10.5281/zenodo.18930044)

The `paper/` directory is intentionally empty. Please download the PDF directly from Zenodo.

---

## Citation

```bibtex
@misc{souzacarvalho2026actionclaim,
  title     = {Toward an Operational Ontology of Agentic Action},
  author    = {Souza Carvalho, Rudson Kiyoshi},
  year      = {2026},
  month     = {March},
  doi       = {10.5281/zenodo.18930044},
  url       = {https://doi.org/10.5281/zenodo.18930044},
  note      = {Preprint}
}
```

---

## License

This work is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).

[![CC BY 4.0](https://licensebuttons.net/l/by/4.0/88x31.png)](https://creativecommons.org/licenses/by/4.0/)
