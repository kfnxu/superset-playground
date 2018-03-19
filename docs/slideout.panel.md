# superset-playground

* goal: allow control-panel to slide out and slide in from leftside.
* what: looks like this one: ![result](/images/slideout.panel.png) <!-- .element height="30%" width="30%" -->
* why: a need to hide and show control-panel in chart container. 
* how: use material-ui Drawer. 

```javascript
integrationoffice/components/ControlPanelsContainer.jsx

import Subheader from 'material-ui/Subheader';
import Toggle from 'material-ui/Toggle';
 	 
+import Drawer from 'material-ui/Drawer';
+import AppBar from 'material-ui/AppBar';
+import RaisedButton from 'material-ui/RaisedButton';

const propTypes = {
   actions: PropTypes.object.isRequired,
     this.getControlData = this.getControlData.bind(this);
     this.state = {
          open: false,
+         drawerOpen: false,
     };
   }
 	 
+  handleNestedListToggle(item){
    this.setState({
       open: item.state.open,
+    });
+  };


     return (
      <div className="row">	      <div className="row">
+       <RaisedButton
+          label="<>"
+          onClick={() => this.setState({drawerOpen: !this.state.drawerOpen})}
+        />
      {/*
      <div className="col-sm-1">
           {this.sectionsToRender().map(section => (

           {
      </div>
      */}
      {/*<div className="col-sm-10">*/}
+     <Drawer width={400} openSecondary={true} open={this.state.drawerOpen} >
       <div className="scrollbar-container">
         <div className="scrollbar-content">
           {this.props.alert &&

           }
                     <List>
                       <Subheader>Nested List Items</Subheader>
+          {this.sectionsToRender().map((section, sectionId) => (
             //console.log("ControlPanelsContainer.jsx section form_data", section, this.props.inj_form_data),	             //console.log("ControlPanelsContainer.jsx section form_data", section, this.props.inj_form_data),
             <ControlPanelSection
	               key={section.label}
	                   ))}
	                 />
                 </ListItem>
               )),]}
+            />
             </ControlPanelSection>
           ))}
             <QueryAndSaveBtns
         </div>
       </div>
       {/*</div>*/}
+      </Drawer>
      </div>
     );
   }

