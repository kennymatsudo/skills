# How well-written technical specs are built

Use this reference when you write, update, or refactor a technical spec or design doc, such as a protocol spec, an API spec, or a team design doc for a feature or service. For a new doc, work through the sections in order. For an existing doc, check it against each section's opening rule and fix what fails.

Each pattern names the spec it comes from. [Sources](#sources) lists the documents: six groups of specs, plus operations guidance for the monitoring section.

## Start with the problem, the scope, and a one-page model

Nearly every spec runs: the problem, goals and non-goals, a one-page overview, the detail, then failure modes, security, compatibility, open questions, and rejected alternatives.

- **Problem first.** Rust's NLL RFC opens with "Problem case #1" through #4, each with code, the current error, and the workaround. PEP 572 rewrites real standard-library code. PEP 703 quotes users who hit the limit.
- **Scope cut on purpose.** Google design docs define non-goals as "things that could reasonably be goals, but are explicitly chosen not to be goals". Rust sorts open questions into resolve before merge, resolve before stabilization, and out of scope.
- **One summary device up front.** Raft's Figure 2 fits the whole algorithm on one page as state, two RPCs, and rules, each rule linked to its section. TLS 1.3 and OAuth 2.0 open with one message-flow diagram whose labeled steps the prose then walks in order. Fetch opens with "A request goes in, a response comes out."
- **A reading map and a place to stop.** The Go generics proposal opens with "This document is long. Here is some guidance on how to read it." QUIC has a Document Structure section grouped by concept. Flexbox tells page authors they can skip its layout algorithm. The Go Memory Model opens with four sentences of advice and an informal model that "should suffice for most programmers", before the formal rules.
- **An order that builds the model.** Bitcoin orders sections so each one fixes the gap the last one left. SQLite's architecture doc and MapReduce follow one request through the system. CommonMark and SQLite's file format go from simple parts to the parts built from them.
- **Rejected ideas phrased as reviewers' questions.** The Go generics proposal asks "Why not use the syntax `F<T>` like C++ and Java?", which turns its alternatives section into an FAQ.

## Keep each section at one level of abstraction

Specs that fail at length usually mix levels on one page.

- **Two layers over the same examples.** A Rust RFC first explains the change "as if it was already included in the language", through examples. Its reference-level section then "should return to the examples given in the previous section" to cover mechanics and corner cases. One doc serves users first and implementers second.
- **Behavior before wire format.** QUIC teaches streams, connections, and loss handling, and holds every byte encoding until its last sections. LSP puts its type definitions before the session lifecycle, so readers meet `InitializeParams` before they know when it is sent.
- **Example first in teaching docs, definition first in reference docs,** with the other following at once. GraphQL shows a query and its response before any grammar. URL opens with "A URL is a struct that represents a universal identifier".
- **Labels for what is binding and who it is for.** QUIC says its diagrams "summarize, not define, protocol elements" and that its state machines are informative. HTML has boxes headed "For web developers (non-normative)". Python marks "CPython implementation detail".
- **Requirement keywords only where they bind.** RFC 2119 says MUST and SHOULD "must be used with care and sparingly", and large RFCs still use 450 to 550 of them out of habit.
- **Freedom left to implementations, shown with its outcomes.** The Go spec writes `x may be [1, 2] or [2, 2]` beside the code, and gives minimum guarantees such as 256-bit constant precision.
- **History kept out of current rules.** TLS 1.3 carries many "Prior to TLS 1.3" notes and `legacy_` fields. Put history in "since version" tags.

## Give every unit the same template

When every message or rule has the same layout, readers skim the familiar parts and read only what differs. The layout is a one-line purpose, the shape (struct, schema, or field table), a literal example, errors with named codes, and a one-clause reason. RFCs, LSP, MCP, OpenAPI, and GraphQL validation rules all follow a version of it.

- **The reason beside the rule, in one clause.** MCP: "Deterministic ordering enables clients to reliably cache the tool list." RFCs put it after the rule ("This avoids situations where..."). MCP's security sections fail this by listing MUSTs with no reasons. Longer rationale goes to an appendix or a citation.
- **Valid and invalid side by side, with the reason on each line.** Go: `T1 struct{ T1 }  // T1 contains a field of T1`. GraphQL labels "Counter Example № 145", and TOML marks lines `# INVALID`. Each pair covers a case in one line.
- **Examples that work as tests.** CommonMark numbers every Markdown input and HTML output pair. The Rust Reference gives each rule an anchor, such as `patterns.ident.binding`, and some anchors link to the compiler tests for that rule.
- **Named rules that always hold.** Raft lists its invariants by name in Figure 3. SemVer has 11 numbered rules that people cite by number.
- **One worked example reused throughout.** Protobuf decodes `08 96 01` byte by byte to the value 150 and reuses those bytes in later examples. PEP 636 grows one text adventure through every pattern-matching feature.
- **Shorthand defined once.** ECMAScript defines its `?` shorthand once by expansion, which saves three lines of error handling at every use.
- **Bold names on algorithm steps.** Flexbox steps read "Freeze over-flexed items", and HTML's later steps cite earlier ones by name. HTML's update-the-rendering steps fail the other way: they nest four to six levels deep with no diagram.
- **Rules outside table cells.** OpenAPI's parameter tables hold encoding requirements among "n/a" cells.
- **No template section with nothing in it,** such as "There are very few drawbacks to this proposal."

## Cover edge cases with general rules, and move the rest out

Large specs (HTTP, HTML, LSP) still run to hundreds of pages. The readable ones manage length with the techniques below, and the short ones (SemVer, TOML, the Raft summary) apply them harder.

- **Specify what can be observed, not how to build it.** ECMAScript says its algorithms "are not intended to imply the use of any specific implementation technique". QUIC lets an implementation use a different state machine "as long as its behavior is consistent". Pinning down only behavior a caller or peer can see removes every case that comes from one implementation's internals.
- **State the general rule, and let edge cases follow from it.** HTTP handles errors in one section (§2.4) and gives each failure a named code. Raft states five named properties, such as Election Safety and Log Matching, so many edge cases reduce to whether a step breaks one of them.
- **Write out an edge case only if it shaped the design.** Raft's Figure 8 shows one crash sequence because it is the reason for a commit rule.
- **Failure gets its own space.** QUIC lists what an on-path attacker can and cannot do. MapReduce has Worker Failure and Master Failure subsections. MCP separates protocol errors from tool errors by whether the model can fix them.
- **Compress cases into tables.** Go's range table covers every input type in a few rows. URL's parsing table shows input, base, valid or not, and output for a dozen edge cases.
- **Link down instead of descending.** SQLite's architecture doc gives each component a paragraph and names its source files. Its file-format doc says "no further information about the format of the wal-index will be provided here". Linking every term fails the other way: HTTP has about 965 section references, and WHATWG prose links nearly every repeated term, so no passage reads on its own.
- **Move material to other documents.** Python splits pattern matching into three PEPs: the spec (634), the rationale (635), and a tutorial (636). TOML keeps its grammar in a separate ABNF file, and MCP keeps its schema in `schema.ts`. Long rationale goes in appendices, and questions in an FAQ.
- **No single giant page.** LSP, OpenAPI, and GraphQL each run 300K to 400K characters on one page, which leaves in-page search as the only navigation.

## Match the diagram to the concept

Draw only where time order, containment, or space matters.

| Concept | Form | Example |
| --- | --- | --- |
| Messages between parties over time | Sequence diagram, time running down, phase labels | TLS 1.3 Figure 1, MCP (Mermaid) |
| Who talks to whom, before mechanics | Box flow with lettered steps and a matching list | OAuth 2.0 Figure 1, MapReduce Figure 1 |
| Modes and transitions | State machine | Raft Figure 4, QUIC stream states |
| Containment or deployment | Nested boxes | MCP architecture, SQLite layers |

Other concepts have their own forms:

- **Byte layout:** struct-like notation (`Version (32)`) or an offset, size, and description table, in place of bit-ruler drawings (QUIC, TLS, SQLite).
- **State with two dimensions:** a grid, such as Raft's logs drawn as entries by index with the term inside each box.
- **Failure:** a strip of panels (a) to (e) whose caption tells the full crash story (Raft Figure 8).
- **Spatial terms:** one labeled picture of the axes, then a gallery with one render per keyword (Flexbox).
- **How an algorithm's state changes:** a small ASCII tree redrawn after each line of input (CommonMark appendix).

Case analysis takes a table. Language references and design proposals use almost no diagrams; code examples and tables carry the structure.

A good figure is introduced in the prose before it appears, walked through after it, and has a caption that explains it without the body text. The hardest sections in the set are about time order and have no diagram: HTML's event loop, the Fetch pipeline, and LSP's lifecycle.

## Define every term at first use, and name the reader

The specs use heavy jargon and define all of it. Terms are defined where first used, in italics or quotes, often by the job they do: Raft's "Terms act as a logical clock". QUIC and TLS add a terminology section, and OAuth borrows security terms from RFC 4949.

The cost of borrowing definitions is dependency. Fetch draws terms from 11 other specs, and QUIC splits its subject across three RFCs.

Good specs name their reader. GraphQL writes for "builders" of servers and tools. HTML swaps in neutral terms such as "in parallel", then translates them for readers who think in threads: "instead of... main thread".

Analogies are rare and one line long. HTTP: "The uniform interface is similar to a window through which one can observe and act upon a thing."

## Specify monitoring as answers to an operator's questions

Protocol and language specs leave monitoring out because they define behavior, not a running service. Design docs for a running system include it, and the best ones organize it around the questions an on-call engineer asks instead of a list of metrics. The Kubernetes KEP template is the strongest model, and Google's SRE books supply the method for choosing what to measure.

**Always include the section.** The IETF draft replacing RFC 5706 says protocol documents "MUST include an 'Operational Considerations' section". A document with nothing to add says "There are no new operations or manageability requirements introduced by this document" and gives a short reason. Google design docs list observability among the cross-cutting concerns checked at review.

**Ask the operator's questions.** The KEP template asks "How can an operator determine if the feature is in use by workloads?", "How can someone using this feature know that it is working for their instance?", "What specific metrics should inform a rollback?", and "Are there any missing metrics that would be useful to have to improve observability of this feature?" It prefers metrics ("Avoid logs or events for this purpose") and reminds authors that "end users cannot usually observe component logs or access metrics." Every metric in the doc answers one of these questions.

**Lead with what users notice.** The SRE book separates symptoms (what users see) from causes (why it happens), and pages on symptoms. Its four golden signals are latency, traffic, errors, and saturation. It tracks the latency of failed requests separately, because "a slow error is even worse than a fast error."

**Define each service-level indicator exactly.** A service-level indicator (SLI) is a measured ratio of good events to valid events. The definition names where it is measured and what that spot misses (server logs miss requests that never arrive), which requests count, and the window. The SRE workbook suggests a four-week rolling window. Kubernetes states its own targets as "99th percentile per cluster-day <= 1s", valid only while load stays under stated limits.

**Give each metric the same fields.** Name, type, unit, labels with their allowed values, the component that emits it, and what value means trouble. KEP-753 (sidecar containers):

```
Metric name: kubelet_started_containers_errors_total
  Type: Counter
  Labels: code, container_type (should be `init_container`)
  Components exposing the metric: kubelet-metrics
  Symptoms: high number of errors indicates that the kubelet is unable to start the sidecar containers
```

OpenTelemetry's semantic conventions add a base unit (`s`, not `ms`), a stability marker, and a requirement level for each attribute. Prometheus names counters with `_total` and durations with `_seconds`.

**Bound every label.** OpenTelemetry requires `http.route` to be low-cardinality and collapses unknown HTTP methods to `_OTHER`. Prometheus advises keeping "the cardinality of your metrics below 10" and rethinking anything past 100. GitLab's user-experience SLI design keeps `correlation_id` in logs only.

**Write rollback triggers as thresholds with a window, a reason, and the action.** KEP-2340: "99th percentile of `apiserver_watch_cache_read_wait` to be below 200ms (2 progress notify pull periods)". KEP-753 gives the order of the rollback: "first disable the feature gate on the control plane and then proceed with the nodes".

**Give each failure mode four lines:** detection through a metric, mitigation, diagnostics, and a test. KEP-1040 (API Priority and Fairness) also says how to tell a bug from real load: long queues with low request volume and low CPU point to a misconfiguration.

**Say what pages a human, and link the rest.** "Every page should be actionable." The SRE workbook alerts on how fast the error budget burns, starting at 2% of the budget in one hour or 5% in six hours for a page, and 10% in three days for a ticket. Exact thresholds, dashboards, and runbooks live in separate docs that the design links to.

**Tie monitoring to rollout stages.** KEPs require a way to turn the feature off at alpha, monitoring answers at beta (when features usually turn on by default), and answers confirmed from production use at GA. KEP-2340 made "Metric `apiserver_watch_cache_read_wait` is implemented" a beta criterion, which guards against metrics "defined but not wired up". The SRE launch checklist adds staged canaries, kill switches, and monitoring of the monitoring system itself.

The common failures are targets left as "N/A" or "`< X` for 99% of requests" (KEP-1287 reached stable with that line), triggers without numbers ("high number of errors", "a long time"), metric lists with no question behind them, no named owner or alert route, and no health signal for the telemetry pipeline.

## Sources

Figures were judged from captions, alt text, and surrounding prose, since the images themselves were not viewed. Very long pages (HTTP, LSP, OpenAPI, GraphQL, the Go spec) were sampled rather than read in full.

- **IETF RFCs:** [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110), [RFC 8446 TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446), [RFC 9000 QUIC](https://www.rfc-editor.org/rfc/rfc9000), [RFC 6749 OAuth 2.0](https://www.rfc-editor.org/rfc/rfc6749), [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119), [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174).
- **Web platform:** [Fetch](https://fetch.spec.whatwg.org), [URL](https://url.spec.whatwg.org), [HTML event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops), [CSS Flexbox 1](https://www.w3.org/TR/css-flexbox-1/), [ECMAScript](https://tc39.es/ecma262/).
- **Language references:** [Go spec](https://go.dev/ref/spec), [Go Memory Model](https://go.dev/ref/mem), [Rust Reference](https://doc.rust-lang.org/reference/), [Python Language Reference](https://docs.python.org/3/reference/), [Lua 5.4 manual](https://www.lua.org/manual/5.4/manual.html).
- **Design proposals:** [PEP 12](https://peps.python.org/pep-0012/), [PEP 572](https://peps.python.org/pep-0572/), [PEP 636](https://peps.python.org/pep-0636/), [PEP 703](https://peps.python.org/pep-0703/), [Rust RFC template](https://github.com/rust-lang/rfcs/blob/master/0000-template.md), [RFC 2094](https://github.com/rust-lang/rfcs/blob/master/text/2094-nll.md), [RFC 2394](https://github.com/rust-lang/rfcs/blob/master/text/2394-async_await.md), [KEP template](https://github.com/kubernetes/enhancements/blob/master/keps/NNNN-kep-template/README.md), [Go type parameters design](https://go.googlesource.com/proposal/+/refs/heads/master/design/43651-type-parameters.md), [Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/).
- **Systems papers and internals:** [Raft](https://raft.github.io/raft.pdf), [SQLite file format](https://sqlite.org/fileformat2.html), [SQLite architecture](https://sqlite.org/arch.html), [Protobuf encoding](https://protobuf.dev/programming-guides/encoding/), [Bitcoin](https://bitcoin.org/bitcoin.pdf), [MapReduce](https://research.google.com/archive/mapreduce-osdi04.pdf).
- **Monitoring and operations:** [KEP template](https://github.com/kubernetes/enhancements/blob/master/keps/NNNN-kep-template/README.md) production readiness sections, [KEP-753](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/753-sidecar-containers/README.md), [KEP-1287](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/1287-in-place-update-pod-resources/README.md), [KEP-2340](https://github.com/kubernetes/enhancements/blob/master/keps/sig-api-machinery/2340-Consistent-reads-from-cache/README.md), [Production readiness review](https://github.com/kubernetes/community/blob/master/sig-architecture/production-readiness.md), [Kubernetes SLOs](https://github.com/kubernetes/community/blob/master/sig-scalability/slos/slos.md), [SRE book: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/), [SRE book: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/), [SRE book: Launch checklist](https://sre.google/sre-book/launch-checklist/), [SRE workbook: Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/), [RFC 5706](https://www.rfc-editor.org/rfc/rfc5706), [draft-ietf-opsawg-rfc5706bis](https://datatracker.ietf.org/doc/draft-ietf-opsawg-rfc5706bis/), [RFC 9312](https://www.rfc-editor.org/rfc/rfc9312), [OpenTelemetry HTTP metrics](https://opentelemetry.io/docs/specs/semconv/http/http-metrics/), [Prometheus instrumentation](https://prometheus.io/docs/practices/instrumentation/), [GitLab user-experience SLIs](https://handbook.gitlab.com/handbook/engineering/architecture/design-documents/user_experience_slis/).
- **API and data formats:** [GraphQL](https://spec.graphql.org), [CommonMark](https://spec.commonmark.org), [SemVer](https://semver.org), [LSP 3.17](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/), [MCP](https://modelcontextprotocol.io/specification), [OpenAPI](https://spec.openapis.org/oas/latest.html), [TOML](https://toml.io).
