# superset-playground

* goal: make control-panel, chart, dashboad can be stand alone or combined, controled by url parameter.
* what: looks like this one: ![result](/images/CollapsibleLists.png) <!-- .element height="30%" width="30%" -->
* why: allow user use them individiually. 
* how: render them individually. 

```javascript
"render_container" is the url parameter to control how is the page rendered for control-panel, chart and dashboard
url:/superset/integrationoffice/dashboard/7/table/108/?form_data={"viz_type":"ihme_choropleth","render_container":"chart",

simpleflow/components/SimpleflowViewContainer.jsx

 queryRequest: PropTypes.object,
 render_container: PropTypes.string,
 };	 

renderChartContainer() {
    return (
      <ChartContainer
        actions={this.props.actions}
        height={this.state.height}
      />
    );
     
  }


+  renderPanelContainer(){
+     return (
+            <ControlPanelsContainer
+              actions={this.props.actions}
+              form_data={this.props.form_data}
+              inj_form_data={this.state.inj_form_data}
+              datasource_type={this.props.datasource_type}
+              onQuery={this.onQuery}
+              onSave={this.toggleModal}
+              onStop={this.onStop}
+              loading={this.props.chartStatus}
+              renderErrorMessage={this.renderErrorMessage}
+              {...this.props}
+            />
+      );
+  }
+
+  renderDashboardContainer(){
+      return (
+             <DashboardViewPage
+                 //this will work, but cause to frequent rendering 
+                 {...this.props}
+                 //queryUpdate={this.queryUpdate}
+             />
+      );
}


render() {
    //if (this.props.standalone) {
    //  return this.renderChartContainer();
    //}

+    console.log('simpleflow/components/SimpleflowViewContainer.jsx', this.props, this.state, this.props.inj_form_data);
+    if ( this.props.render_container){ 
+     switch(this.props.render_container){
+       case 'panel': 
+                   return this.renderPanelContainer();
+                   break;
+       case 'chart':
+                   return this.renderChartContainer();
+                   break;
+       case 'dashboard': 
+                   return this.renderDashboardContainer();
+                   break;
+       default: 
+                   //return this.renderAllContainers(); 
+                   break;
+     }
     }
+
   queryRequest: state.queryRequest,
     ////inject form data
     inj_form_data: state.inj_form_data,
     render_container: state.render_container,
   };
 }


simpleflow/view.jsx
+   const render_container = bootstrapData.form_data['render_container'] ?bootstrapData.form_data['render_container'] : "all"; 

    triggerQuery: true,
    triggerRender: false,
    alert: null,
+   render_container: render_container,
    },
    );

