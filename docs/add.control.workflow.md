# superset-playground

* goal: workflow for adding or enabling a 'input-control' in control-panel. 
* what: looks like this one: ![result](/images/pubsub.png) <!-- .element height="30%" width="30%" -->
* why: there is hard-coded ( will change ) mask on the server to limit the 'controls' as filters.
* how: map both graph-db data-set to database column-id and front-end control name. 

```javascript
mask_json = '{"model_group":"model_id","sex_group":"sex_id","age_select":"age_group_id","location":"location_id", "cause":"cause_id", "risk":"risk_id"}'
"model_group" is a property of a node in graph-db. "SearchCategory" is the node, "model_group" is one of the property "tcat".
"model_group" is also a control name defined in "stores/controls.jsx".
"sf_model_group" is the map data set in "stores/controls.jsx" for the control.
"model_id" is a database table column "model_id" which should in the result of the sql for the "chart".

MATCH (a:SearchCategory ) WHERE a.tcat in ["model_group"] RETURN a.tid AS ID, a.tname AS NAME, a.tcat as CATEGORY order by toInteger(a.tid), a.tname;MATCH (a:SearchCategory )

mask_json are defined in these server-side python code:
superset/plugins/internal/simpleflow.py
superset/views/core.py

graph-db query for GBD-ui:
superset/graph.py

front-end control defined in:
superset/assets/javascripts/integrationoffice/stores/controls.jsx

