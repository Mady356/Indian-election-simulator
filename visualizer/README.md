# India Election + Demographics Visualizer

Local static visual explorer for the state-first election/demographic workflow.

## Build Data

From the project root:

```bash
venv/bin/python -m src.visualization.build_visualizer_data
```

This writes:

```text
visualizer/data/election_demographics_bundle.json
```

The bundle is relational:

* `states`
* `districts`
* `state_party_swings`
* `constituencies`
* `state_from_districts`

## Run

From the project root:

```bash
venv/bin/python -m http.server 8000
```

Open:

```text
http://localhost:8000/visualizer/
```

## Current Map Status

The app currently uses a state grid/cartogram because the repo does not yet
contain India state/district boundary GeoJSON.

To show real district polygons, add boundary files later, for example:

```text
data/geography/india_states.geojson
data/geography/india_districts_2011.geojson
```

Useful join keys would be:

* state name / Census state code
* district name / Census district code

Once those files exist, the visualizer can replace the grid with true
state/district maps while keeping the same data bundle.
