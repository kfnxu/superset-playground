match (a:VisSection {tname: "default"}), (b:VisControlRow ) where b.tname = 'model_group' create (a) - [:contains] -> (b);
match (a:VisSection {tname: "single"}) - [r:contains] -> (b:VisControlRow {pos: 7, tname: "model_group"}) delete r;
match(a:VisContainer), (b:SearchCategory) where a.tname = 'single' and b.tcat = 'charttype' and b.tname = 'simpleflow_line' create (a)-[r:has]->(b);
match(a:VisContainer), (b:SearchCategory) where a.tname = 'single' and b.tcat = 'charttype' and b.tname = 'simpleflow_bar' create (a)-[r:has]->(b);
match(a:VisContainer), (b:SearchCategory) where a.tname = 'single' and b.tcat = 'charttype' and b.tname = 'simpleflow_area' create (a)-[r:has]->(b);
match(a:VisContainer), (b:SearchCategory) where a.tname = 'single' and b.tcat = 'charttype' and b.tname = 'simpleflow_compare' create (a)-[r:has]->(b);
match(a:VisContainer), (b:SearchCategory) where a.tname = 'single' and b.tcat = 'charttype' and b.tname = 'treemap' create (a)-[r:has]->(b);
match(a:VisContainer), (b:SearchCategory) where a.tname = 'single' and b.tcat = 'charttype' and b.tname = 'world_map' create (a)-[r:has]->(b);
match(a:VisContainer), (b:SearchCategory) where a.tname = 'explore' and b.tcat = 'charttype' and b.tname = 'world_map' create (a)-[r:has]->(b);
match(a:VisContainer), (b:SearchCategory) where a.tname = 'explore' and b.tcat = 'charttype' and b.tname = 'sankey' create (a)-[r:has]->(b);
match(a:VisContainer), (b:SearchCategory) where a.tname = 'explore' and b.tcat = 'charttype' and b.tname = 'simpleflow_line' create (a)-[r:has]->(b);
match(a:VisContainer), (b:SearchCategory) where a.tname = 'explore' and b.tcat = 'charttype' and b.tname = 'simpleflow_bar' create (a)-[r:has]->(b);
match(a:VisContainer), (b:SearchCategory) where a.tname = 'explore' and b.tcat = 'charttype' and b.tname = 'simpleflow_area' create (a)-[r:has]->(b);
match(a:VisContainer), (b:SearchCategory) where a.tname = 'explore' and b.tcat = 'charttype' and b.tname = 'simpleflow_compare' create (a)-[r:has]->(b);

match (f:VisSection {tname: "FBD Compare"}) set f.tid = 1;
match (f:VisSection {tname: "Shared Setting"}) set f.tid = 2;
match (f:VisSection {tname: "Line Setting"}) set f.tid = 3;
match (f:VisSection {tname: "Map Setting"}) set f.tid = 3;
match (f:VisSection {tname: "Treemap Setting"}) set f.tid = 4;
match (f:VisSection {tname: "Map Setting"}) set f.tid = 5
match (f:VisSection {tname: "Sankey Setting"}) set f.tid = 6;
match (f:VisSection) return f; 

match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "11" and f.tid in [ 1, 2, 5 ] create (s)-[r:has] -> (f);
match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "2" and f.tid in [ 1, 2, 4 ] create (s)-[r:has] -> (f);
match (s:SearchCategory {tcat: "charttype"} ) - [r:has] - (f:VisSection) return s.tname, r, f.tname order by s.tname;

match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "5" and f.tid in [ 1, 2, 3 ] create (s)-[r:has] -> (f);
match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "6" and f.tid in [ 1, 2, 3 ] create (s)-[r:has] -> (f);
match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "7" and f.tid in [ 1, 2, 3 ] create (s)-[r:has] -> (f);
match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "1" and f.tid in [ 1, 2, 5 ] create (s)-[r:has] -> (f);
match (f:VisSection), (s:SearchCategory {tcat: "charttype"}) where s.tid = "8" and f.tid in [ 1, 2, 3 ] create (s)-[r:has] -> (f);


