# Archaeological stratigraphy data model (draft)

Draft written from general knowledge. It has **not** been checked against the literature or by a field archaeologist: vocabulary and rules must be reviewed before fixing version 1. Only `units` and `relations` are implemented in 0.1; the rest is the target design.

## 1. Principles

- **Recording and derivation are separate.** Observed facts (physical relations, measurements, datings) are stored; temporal order, phases and the diagram are derived.
- **Every assertion carries certainty and source** (certain, probable, doubtful).
- **Absence of a relation is not contemporaneity.**
- **A unit is not a date.** Chronology is a set of dating assertions.
- **Verifiable**, with a report explaining which row fails and why.
- **Open files**: one CSV per entity, UTF-8, stable identifiers.

## 2. Overview

All tables join to the unit by `unit_id`: `relations` (unit to unit), `points` and `geometries`, `finds` (and specialised tables), `samples`, `photos` and `drawings`, `datings` and `groupings`. `datings` also applies to finds, samples and phases.

## 3. Stratigraphic unit (`units`)

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `unit_id` | text | yes | Unique key within the site. Text, to allow "1045b". |
| `site` | text | no | To join campaigns. |
| `area`, `sector`, `square` | text | no | Location. |
| `unit_type` | vocabulary | yes | `deposit`, `interface`, `structure`, `virtual`. |
| `subtype` | vocabulary | no | Cut, pit, trench, wall, floor, fill, collapse... |
| `description` | text | no | What is observed, without interpretation. |
| `interpretation` | text | no | What is inferred. |
| `excavation_status` | vocabulary | no | `unexcavated`, `partial`, `excavated`, `documented_only`. |
| `date_start`, `date_end` | ISO date | no | Excavation dates. |
| `recorder` | text | no | |
| `reliability` | vocabulary | no | good, fair, poor. |
| `notes` | text | no | |

`deposit` = positive unit; `interface` = negative unit; `structure` = built unit; `virtual` = reconstructed, not excavated (Extended Matrix).

Physical attributes by type (colour, texture, compaction; shape, profile, edges; material, bonding...): proposed as a long-format table `unit_attributes` (`unit_id`, `attribute`, `value`). Undecided.

## 4. Spatial position (`points`, `geometries`, `reference_systems`)

- `reference_systems`: global (EPSG) or local system with its transformation; vertical datum.
- `points`: `point_id`, `unit_id`, `role` (`top_level`, `bottom_level`, `centre`, `boundary`, `corner`, `find`), `x`, `y`, `z` (m), `system_id`, `method` (`total_station`, `gnss`, `tape`, `photogrammetry`, `estimated`), `precision_m`, `measured_on`.
- `geometries`: polygon in plan or section (WKT/GeoJSON) with `unit_id`, `type` (`plan`, `section`, `conjectural_limit`), `system_id`, `method`.
- Derived, not stored: mean levels, thickness, area, approximate volume, depth relative to a datum.

## 5. Relations (`relations`)

`relations`: `rel_id`, `from_unit`, `type`, `to_unit`, `certainty`, `source` (`field`, `section`, `photograph`, `inference`, `other`), `observed_by`, `date`, `notes`. Each relation is written once; the inverse is generated. Inverse names are also accepted on input and normalised.

| Type | Inverse | Temporal effect | Allowed origin | Allowed destination |
| --- | --- | --- | --- | --- |
| `covers` | `covered_by` | origin later than destination | deposit, structure | any |
| `cuts` | `cut_by` | origin later than destination | interface | any |
| `fills` | `filled_by` | origin later than destination | deposit | interface |
| `rests_on` | `supports` | origin later than destination | deposit, structure | any |
| `bonded_to` | `bonded_to` | contemporary | structure | structure |
| `same_as` | `same_as` | same unit recorded twice | any | same type |
| `later_than` | `earlier_than` | origin later, no physical contact | any | any |

- Types are vocabulary rows, not code: adaptable to each school.
- `same_as` merges nodes; it produces no edge.
- Contemporaneity is never inferred from the absence of a relation.

## 6. Chronology (`datings`)

Dating assertions about an object (`unit`, `find`, `sample`, `phase`, `grouping`): `dating_id`, `object_type`, `object_id`, `method` (`radiocarbon`, `dendrochronology`, `thermoluminescence`, `archaeomagnetism`, `typology`, `numismatics`, `epigraphy`, `documentary`, `other`), `meaning` (`event`, `terminus_post_quem`, `terminus_ante_quem`, `use`), `association` (`contemporary`, `residual`, `intrusive`, `unknown`), `year_start`, `year_end` (signed astronomical year), `uncertainty`, `age_14c`, `error_14c`, `calibration_curve`, `lab_ref`, `certainty`, `reference`.

What is dated is not the context: `association` makes this explicit.

## 7. Associated material

`finds` (common) and specialised `pottery`, `lithics`, `fauna`, `human_remains` (sensitive data); `samples`; `photos` + `photo_objects` (photo-object link); `drawings`. Datings of finds and samples live in `datings`.

## 8. Groupings (`groupings`, `grouping_units`)

Levels: `activity`, `structure`, `space`, `phase`, `period`. `groupings`: `grouping_id`, `type`, `name`, `description`, `parent_id`, `certainty`. A unit may belong to several groupings of different types, but to a single phase. Phases are proposed from the graph and confirmed by hand.

## 9. Verification (`verify`)

Severities: **error**, **warning**, **info**. Non-zero exit code when there are errors. Implemented rules are marked ✔.

| Rule | Checks | Severity | |
| --- | --- | --- | --- |
| R01 | Duplicate `unit_id` | error | ✔ |
| R02 | Reference to a missing unit | error | ✔ |
| R03 | Relation type outside the vocabulary | error | ✔ |
| R04 | Relation between disallowed unit types | error | ✔ |
| R05 | Unit related to itself | error | ✔ |
| R06 | Invalid vocabulary value (unit type, certainty) | error | ✔ |
| R10 | Cycle in the temporal graph (with the path) | error | ✔ |
| R11 | Direct contradiction (A covers B and B covers A) | error | ✔ |
| R12 | Cycle when merging `same_as` | error | ✔ |
| R13 | `same_as` between different types | warning | ✔ |
| R14 | Cut without fill, or fill without cut | warning | ✔ |
| R15 | Unit without relations | warning | ✔ |
| R16 | Relation redundant by transitivity | info | ✔ |
| R17 | Inverse written both ways with different data | warning | |
| R20 | Bottom level higher than top level | error | |
| R21 | Invalid geometry or outside the site | error | |
| R22 | A covers B but is clearly below it (with tolerance) | warning | |
| R23 | A covers or cuts B but the polygons do not touch | warning | |
| R30 | Dating of an earlier unit more recent than that of a later one | error if both certain; warning otherwise | |
| R31 | `terminus_post_quem` later than `terminus_ante_quem` in the same unit | error | |
| R32 | Phase inconsistent with the order | error | |
| R33 | Unit dated with a residual or intrusive object | warning | |
| R34 | Dating propagated through the sequence leaves an empty interval | error | |

Datings are propagated through the graph. Spatial rules are warnings, with configurable tolerances. Report in text and JSON.

## 10. Graphical output (`render`)

Editable SVG: one node per unit (or `same_as` group), shape by type, rows by sequence level, stroke by certainty (solid, dashed, dotted), cycles in red. Nodes have `id="unit-1045"` and `data-type`; styles are embedded. Planned: optional phase bands, named layers, `data-phase`, a better layout algorithm (long-edge routing), DOT, GraphML, and a CSV with the computed order. The SVG is output only.

## 11. Files and compatibility

A project folder with one CSV per table (later also `project.json`: name, site, `schema_version`, tolerances). UTF-8, comma, decimal point, ISO 8601 dates, identifiers as text. Planned [hmdp](https://www.iosa.it/specs/harris-matrix-data-package/) adapter: `contexts` <-> `units`, `observations` <-> `relations`, `inferences` <-> `same_as`, `phases`/`periods` <-> `groupings`, `events` <-> `datings` (lossy: certainty, source, position and materials are dropped).

## 12. Standing-buildings archaeology

To be designed: on elevations and walls the relation is observed on a wall face, so the face and the position on the wall should be recorded (wall units), along with specific relation types (bonded, abutting, cut by opening, repair) and grouping into building elements and construction phases. The base model must support this without structural changes.

## 13. Open questions

- Relation vocabulary: is it enough? What is missing (bonds with, bears on...)?
- Convention: strict single-context units, or also wall units (USM/UEM)? Keep `virtual`?
- Physical attributes: columns per type or long format?
- Identifiers: unique per site or per campaign?
- Chronology: signed astronomical year or BC/AD? Store calibration data?
- Phases: automatic proposals or only recorded?
- Space: tolerances for R22 and R23; is 3D needed?
- Human remains: common or separate schema?
- SVG: output only, or import edits back?
- Wide input format (one row per unit with `covers`, `cuts`... columns holding `;`-separated lists) as a convenience over `relations.csv`.
- Nanopublications: optional export of relations and datings (certainty and source as provenance)? Requires stable identifiers (URIs) and a decision on what is published.
- Bibliography: check against the original sources before v1.
- Licence.
