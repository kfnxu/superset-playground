import simplejson as json
from superset import app
##pip install neo4jrestclient
from neo4jrestclient.client import GraphDatabase
config = app.config

class BaseGraph(object):

    def __init__(self):
        host = config.get("GRAPHDB_HOST") #""
        user = config.get("GRAPHDB_USER") #""
        pw = config.get("GRAPHDB_PW") #""
        self.db = GraphDatabase(host, username=user, password=pw)

    def get_search_categories_graph_db(self, in_vis_type="line", in_vis_id="1", in_vis_container_id="1"):
        vis_id = str(1)
        if int(in_vis_id) > 0:
           vis_id = in_vis_id
        vis_container_id = str(1) 
        if int(in_vis_container_id) > 0:
           vis_container_id = in_vis_container_id
        q  = 'match(a:VisContainer) - [r:has] - (p) where a.tid=' + str(vis_id) + ' '
        q += 'return p.tid as ID, p.tname as NAME, p.tcat as CATEGORY order by toInteger(p.tid) '
        q += 'union MATCH (a:SearchCategory ) WHERE a.tcat in ["measure", "cause", "risk", "location", "age_group", "sex", "unit", "vistype", "viscontainer", "model_version", "year_group"] RETURN a.tid AS ID, a.tname AS NAME, a.tcat as CATEGORY order by toInteger(a.tid), a.tname'
        print('get_search_categories_graph_db vis_id, vis_container_id, q', in_vis_id, in_vis_container_id, q)
        results = self.db.query(q, returns=(str, unicode, str))
        ### how to use dataset
        #for r in results:
        #   print("(%s)-[%s]-[%s]" % (r[0], r[1], r[2]))
        return results


    def get_search_setting_graph_db(self, in_vis_type="line", in_vis_id="1", in_vis_container_id="1"):
       print("get_search_setting_graph_db in_vis_type, in_vis_id, in_vis_container_id", in_vis_type, in_vis_id, in_vis_container_id)
       vis_id = str(1)
       if int(in_vis_id) > 0:
           vis_id = in_vis_id
       vis_container_id = str(1)
       if int(in_vis_container_id) > 0:
           vis_container_id = in_vis_container_id
       #q = 'match (a:dataResult {tname:"forecasting"}) - [:contains] -> (f:VisSection {tname:"FBD Compare"}) - [:contains] ->  (g:VisControlRow) - [:contains] -> (h:VisControl) return a.tname, f.tname, g.tname, h.tname order by f.tname, g.pos union match ( a:dataResult {tname:"forecasting"}) - [:typeOf] -> (b:Visualization {tid:' + str(vis_id) + '}) - [r2:typeOf] -> (c:VisContainer {tid:' + str(vis_container_id) + '} ) - [:contains] -> (d:VisView {tname:"simpleFlowView"}) -[:contains] -> (e:VisControlPanel) -[:contains] -> (f:VisSection) - [:contains] -> (g:VisControlRow) - [:contains] -> (h:VisControl)    return a.tname,f.tname, g.tname, h.tname order by toInteger(f.pos), toInteger(g.pos)'

       q = 'match (a:dataResult {tname:"forecasting"}) - [:contains] -> (f:VisSection {tname:"FBD Compare"}) - [:contains] ->  (g:VisControlRow) - [:contains] -> (h:VisControl) return a.tname, f.tname, g.tname, h.tname order by f.tname, g.pos union match (s:SearchCategory {tcat: "charttype", tname:"' + str(in_vis_type) + '"} ) - [r:has] - (f:VisSection) with f match ( a:dataResult {tname:"forecasting"}) - [:typeOf] -> (b:Visualization {tid:' + str(vis_id) + '}) - [r2:typeOf] -> (c:VisContainer {tid:' + str(vis_container_id) + '} ) - [:contains] -> (d:VisView {tname:"simpleFlowView"}) -[:contains] -> (e:VisControlPanel) -[:contains] -> (f) - [:contains] ->  (g:VisControlRow) - [:contains] -> (h:VisControl) return a.tname, f.tname, g.tname, h.tname order by g.pos';
       results = self.db.query(q, returns=(str, str, str, str))
       print("get_search_setting_graph_db results q", q, results)
       return results


