/* eslint camelcase: 0 */
import React from 'react';
import PropTypes from 'prop-types';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { Alert } from 'react-bootstrap';
import { sectionsToRender } from '../stores/visTypes';
import ControlPanelSection from './ControlPanelSection';
import ControlRow from './ControlRow';
import Control from './Control';
import controls from '../stores/controls';
/* move down from integrationofficeview */
import QueryAndSaveBtns from './QueryAndSaveBtns';
import * as actions from '../actions/integrationofficeActions';

/* ui to hide/show */
import {List, ListItem} from 'material-ui/List';
import ActionGrade from 'material-ui/svg-icons/action/grade';
import ContentInbox from 'material-ui/svg-icons/content/inbox';
import ContentDrafts from 'material-ui/svg-icons/content/drafts';
import ContentSend from 'material-ui/svg-icons/content/send';
import Subheader from 'material-ui/Subheader';
import Toggle from 'material-ui/Toggle';


const propTypes = {
  actions: PropTypes.object.isRequired,
  alert: PropTypes.string,
  datasource_type: PropTypes.string.isRequired,
  integrationofficeState: PropTypes.object.isRequired,
  controls: PropTypes.object.isRequired,
  form_data: PropTypes.object.isRequired,
  isDatasourceMetaLoading: PropTypes.bool.isRequired,
  inj_form_data: PropTypes.object.isRequired,

  onQuery: PropTypes.func, 
  onStop: PropTypes.func,
  toggleModal: PropTypes.func, 
  renderErrorMessage: PropTypes.func,
 
};


class ControlPanelsContainer extends React.Component {

  constructor(props) {
    super(props);
    this.removeAlert = this.removeAlert.bind(this);
    this.getControlData = this.getControlData.bind(this);
    this.state = {
         open: false,
    };
  }

  handleToggle(){
    this.setState({
      open: item.state.open,
    })
  }

  handleNestedListToggle(item){
    this.setState({
      open: item.state.open,
    });
  };

  getControlData(controlName) {
    const mapF = controls[controlName].mapStateToProps;
    if (mapF) {
      return Object.assign({}, this.props.controls[controlName], mapF(this.props.integrationofficeState));
    }
    return this.props.controls[controlName];
  }
  sectionsToRender() {
    ////primaryly to test the dynamic generate controlsection, controlsecrows, controlname
    //return sectionsToRender(this.props.form_data.viz_type, this.props.datasource_type);
    return this.props.inj_form_data.search_dependencies_controlSections;
  }
  removeAlert() {
    this.props.actions.removeControlPanelAlert();
  }

  // call parent function for supporting move queryandsave down to this one
  onQuery() {
    this.props.onQuery();
  }

  onStop() {
    this.props.onStop(); 
  }

  toggleModal() {
    this.props.toggleModal(); 
  }
  
  renderErrorMessage(){ 
    this.props.renderErrorMessage(); 
  }

  render() {
    ////this setion of code is for check if there is no ajax data from integrationoffice_json
    ////then set to empty
    if ( !this.props.inj_form_data || !this.props.inj_form_data.search_dependencies_controlSections )
    {
       return ( <div /> )
    }
 
    return (
     <div className="row">
     {/*
     <div className="col-sm-1">
          {this.sectionsToRender().map(section => (
            //console.log("ControlPanelsContainer.jsx section form_data", section, this.props.inj_form_data),
              section.controlSetRows.map((controlSets, i) => (
                //console.log("ControlPanelsContainer.jsx controlSets i", controlSets, i),
                  controlSets.map(controlName => (
                    //console.log("ControlPanelsContainer.jsx controlName", controlName, this.props.controls),
                    controlName && controlName == 'viz_type' && this.props.controls[controlName] &&
                      <div>
                      <br />
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
                      </div>
                  ))
              ))
          ))}

     </div>
     <div className="col-sm-1">
        <div style={{borderRight:"1px solid #d2d2d2",height:"80%", marginTop: "30px"}}>
        </div>
     </div>
     */}
     {/*<div className="col-sm-10">*/}
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
     {/*</div>*/}
     </div>
    );
  }
}

ControlPanelsContainer.propTypes = propTypes;

function mapStateToProps(state) {
  return {
    alert: state.controlPanelAlert,
    isDatasourceMetaLoading: state.isDatasourceMetaLoading,
    controls: state.controls,
    integrationofficeState: state,
    inj_form_data: state.inj_form_data,
  };
}

function mapDispatchToProps(dispatch) {
  return {
    actions: bindActionCreators(actions, dispatch),
  };
}

export { ControlPanelsContainer };

export default connect(mapStateToProps, mapDispatchToProps)(ControlPanelsContainer);
