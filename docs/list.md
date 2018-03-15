# superset-playground

* goal: make control-panel items to nested list which can be Collapsible Lists.
* what: looks like this one: ![result](/images/collapsiblelists.png) <!-- .element height="30%" width="30%" -->
* why: to organiz items into categories.
* how: use material-ui nested list.

```javascript
integrationoffice/components/ControlPanelsContainer.jsx
+/* ui to hide/show */
+import {List, ListItem} from 'material-ui/List';
+import ActionGrade from 'material-ui/svg-icons/action/grade';
+import ContentInbox from 'material-ui/svg-icons/content/inbox';
+import ContentDrafts from 'material-ui/svg-icons/content/drafts';
+import ContentSend from 'material-ui/svg-icons/content/send';
+import Subheader from 'material-ui/Subheader';
+import Toggle from 'material-ui/Toggle';


integrationoffice/components/ControlPanelsContainer.jsx
class ControlPanelsContainer extends React.Component {

  constructor(props) {
    super(props);
    this.removeAlert = this.removeAlert.bind(this);
    this.getControlData = this.getControlData.bind(this);

+    this.state = {
+         open: false,
+    };
+  }
+
+  handleToggle(){
+    this.setState({
+      open: item.state.open,
+    })
   }	   
+
+  handleNestedListToggle(item){
+    this.setState({
+      open: item.state.open,
+    });
+  };
+

integrationoffice/components/ControlPanelsContainer.jsx

  render() {
    ////this setion of code is for check if there is no ajax data from integrationoffice_json
    ////then set to empty
    if ( !this.props.inj_form_data || !this.props.inj_form_data.search_dependencies_controlSections )
    {
       return ( <div /> )
    }
    return (
     <div className="row">
      <div className="scrollbar-container">
        <div className="scrollbar-content">
          {this.props.alert &&
            <Alert bsStyle="warning">
              {this.props.alert}
              <i
                className="fa fa-close pull-right"
                onClick={this.removeAlert}
                style={{ cursor: 'pointer' }}
              />
            </Alert>
          }
          <List>
            <Subheader>Nested List Items</Subheader>
          {this.sectionsToRender().map(section => (
            //console.log("ControlPanelsContainer.jsx section form_data", section, this.props.inj_form_data),
            <ControlPanelSection
              key={section.label}
              label={section.label}
              tooltip={section.description}
            >
            <ListItem
              primaryText={section.label}
              leftIcon={<ContentInbox />}
              initiallyOpen={false}
              primaryTogglesNestedList={true}   
              nestedItems=
              {[section.controlSetRows.map((controlSets, i) => (
                //console.log("ControlPanelsContainer.jsx controlSets i", controlSets, i),
                <ListItem
                  key={i}
                  primaryText=""
                  leftIcon={<ActionGrade />}
                >
                <ControlRow
                  key={`controlsetrow-${i}`}
                  controls={controlSets.map(controlName => (
                    ////console.log("ControlPanelsContainer.jsx controlName", controlName, this.props.controls), 
                    //controlName && controlName != 'viz_type' && this.props.controls[controlName] &&
                      <Control
                        name={controlName}
                        key={`control-${controlName}`}
                        value={this.props.form_data[controlName]}
                        validationErrors={this.props.controls[controlName].validationErrors}
                        actions={this.props.actions}
                        ////pass form_data to control 
                        form_data={this.props.form_data}
                        {...this.getControlData(controlName)}
                      />
                  ))}
                />
                </ListItem>
                
              )),]}
            /> 
            </ControlPanelSection>
          ))}
            <QueryAndSaveBtns
              canAdd="True"
              onQuery={this.onQuery.bind(this)}
              onSave={this.toggleModal.bind(this)}
              onStop={this.onStop.bind(this)}
              loading={this.props.chartStatus === 'loading'}
              errorMessage={this.renderErrorMessage.bind(this)}
            />
            <br />
            <br />
            <br />
           </List>
        </div>
      </div>
     </div>
    );
  }

