# superset-playground

* goal: add new dependency for dynamic chart-setting.
* what: looks like this one: ![result](/images/slideout.panel.png) <!-- .element height="30%" width="30%" -->
* why: to allow each chart-type to have its own setting.
* how: create a relationship between SerachCategory propertis 'charttype' with VisSection in graph-db. 

```javascript
graph-db/update.relationship.cypher

+
+match (f:VisSection {tname: "FBD Compare"}) set f.tid = 1;
+match (f:VisSection {tname: "Shared Setting"}) set f.tid = 2;
+match (f:VisSection {tname: "Line Setting"}) set f.tid = 3;
+match (f:VisSection {tname: "Map Setting"}) set f.tid = 3;
+match (f:VisSection {tname: "Treemap Setting"}) set f.tid = 4;
+match (f:VisSection {tname: "Map Setting"}) set f.tid = 5
+match (f:VisSection {tname: "Sankey Setting"}) set f.tid = 6;
+match (f:VisSection) return f; 
+
+match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "11" and f.tid in [ 1, 2, 5 ] create (s)-[r:has] -> (f);
+match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "2" and f.tid in [ 1, 2, 4 ] create (s)-[r:has] -> (f);
+match (s:SearchCategory {tcat: "charttype"} ) - [r:has] - (f:VisSection) return s.tname, r, f.tname order by s.tname;
+
+match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "5" and f.tid in [ 1, 2, 3 ] create (s)-[r:has] -> (f);
+match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "6" and f.tid in [ 1, 2, 3 ] create (s)-[r:has] -> (f);
+match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "7" and f.tid in [ 1, 2, 3 ] create (s)-[r:has] -> (f);
+match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "1" and f.tid in [ 1, 2, 5 ] create (s)-[r:has] -> (f);
+match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "8" and f.tid in [ 1, 2, 3 ] create (s)-[r:has] -> (f);
+
+

```javascript
superset/graph.py

+
+       q = 'match (a:dataResult {tname:"forecasting"}) - [:contains] -> (f:VisSection {tname:"FBD Compare"}) - [:contains] ->  (g:VisControlRow) - [:contains] -> (h:VisControl) return a.tname, f.tname, g.tname, h.tname order by f.tname, g.pos union match (s:SearchCategory {tcat: "charttype", tname:"' + str(in_vis_type) + '"} ) - [r:has] - (f:VisSection) with f match ( a:dataResult {tname:"forecasting"}) - [:typeOf] -> (b:Visualization {tid:' + str(vis_id) + '}) - [r2:typeOf] -> (c:VisContainer {tid:' + str(vis_container_id) + '} ) - [:contains] -> (d:VisView {tname:"simpleFlowView"}) -[:contains] -> (e:VisControlPanel) -[:contains] -> (f) - [:contains] ->  (g:VisControlRow) - [:contains] -> (h:VisControl) return a.tname, f.tname, g.tname, h.tname order by g.pos';
        results = self.db.query(q, returns=(str, str, str, str))


```javascript
superset/plugins/internal/simpleflow.py

         vis_container_id = form_data.get("viscontainer_group", 1)
         vis_id = form_data.get("vistype_group", 1)
+        search_setting = self.baseGraph.get_search_setting_graph_db(viz_type_form, vis_container_id, vis_id)
         #build setting array
         panel = {}
         sections = []
         form_data['search_dependencies_controlSections'] =  sections
 	 
         ##rebuild form_data for data from graph-db	         ##rebuild form_data for data from graph-db
+        search_categories = self.baseGraph.get_search_categories_graph_db(viz_type_form, vis_container_id, vis_id)
         search_categories_array = []
         ##clear all form_data related to setting, can be more effecient 
         vis_id = form_data.get("vistype_group", 1)
+        viz_type_form = form_data.get("viz_type",1)
+        search_setting = self.baseGraph.get_search_setting_graph_db(viz_type_form, vis_container_id, vis_id)

+        search_categories = self.baseGraph.get_search_categories_graph_db(viz_type_form, vis_container_id, vis_id)


superset/views/core.py

         vis_container_id = form_data.get("viscontainer_group", 1)
         vis_id = form_data.get("vistype_group", 1)
+        viz_type_form = form_data.get("viz_type", 1)
+        search_categories = self.get_search_categories_graph_db(viz_type_form, vis_container_id, vis_id)

