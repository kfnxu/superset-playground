/* eslint camelcase: 0 */
import React from 'react';
import PropTypes from 'prop-types';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import ChartContainer from './ChartContainer';
import ControlPanelsContainer from './ControlPanelsContainer';
import SaveModal from './SaveModal';
import QueryAndSaveBtns from './QueryAndSaveBtns';
import { getSimpleflowUrl } from '../simpleflowUtils';
import * as actions from '../actions/simpleflowActions';
import { getFormDataFromControls } from '../stores/store';

import DashboardViewPage    from '../../dashboard/view';

const propTypes = {
  actions: PropTypes.object.isRequired,
  datasource_type: PropTypes.string.isRequired,
  chartStatus: PropTypes.string,
  controls: PropTypes.object.isRequired,
  forcedHeight: PropTypes.string,
  form_data: PropTypes.object.isRequired,
  standalone: PropTypes.bool.isRequired,
  triggerQuery: PropTypes.bool.isRequired,
  queryRequest: PropTypes.object,
  render_container: PropTypes.string,
};

class SimpleflowViewContainer extends React.Component {
  constructor(props) {
    super(props);
    this.queryUpdate = 1; 
    this.state = {
      height: this.getHeight(),
      showModal: false,
    };
  }

  componentDidMount() {
    console.log('SimpleflowViewContainer componentDidMount');
    if (!this.props.standalone) {
      this.props.actions.fetchDatasources();
    }
    window.addEventListener('resize', this.handleResize.bind(this));
    this.triggerQueryIfNeeded();
  }

  componentWillReceiveProps(np) {
    if ( np.controls.viz_type && this.props.controls.viz_type && np.controls.viz_type.value !== this.props.controls.viz_type.value) {
      this.props.actions.resetControls();
      this.props.actions.triggerQuery();
    }
    if ( np.controls.datasource && this.props.controls.datasource && np.controls.datasource.value !== this.props.controls.datasource.value) {
      this.props.actions.fetchDatasourceMetadata(np.form_data.datasource, true);
    }
  }

  componentDidUpdate() {
    console.log('SimpleflowViewContainer componentDidUpdate');
    this.triggerQueryIfNeeded();
  }

  componentWillUnmount() {
    window.removeEventListener('resize', this.handleResize.bind(this));
  }

  onQuery() {
    // remove alerts when query
    this.props.actions.removeControlPanelAlert();
    this.props.actions.removeChartAlert();

    this.props.actions.triggerQuery();
    // for triggeringdashboard to refresh
    // this.queryUpdate ++; 
    console.log('dashboard/view.js onQuery', this.queryUpdate);
    history.pushState(
      {},
      document.title,
      getSimpleflowUrl(this.props.form_data));
  }

  onStop() {
    this.props.actions.chartUpdateStopped(this.props.queryRequest);
  }

  getHeight() {
    if (this.props.forcedHeight) {
      return this.props.forcedHeight + 'px';
    }
    const navHeight = this.props.standalone ? 0 : 90;
    return `${window.innerHeight - navHeight}px`;
  }


  triggerQueryIfNeeded() {
    console.log('components/SimpleflowViewContainer.jsx triggerQueryIfNeeded', this.props.triggerQuery);
    if (this.props.triggerQuery && !this.hasErrors()) {
      this.props.actions.runQuery(this.props.form_data);
    }
  }

  handleResize() {
    clearTimeout(this.resizeTimer);
    this.resizeTimer = setTimeout(() => {
      this.setState({ height: this.getHeight() });
    }, 250);
  }

  toggleModal() {
    this.setState({ showModal: !this.state.showModal });
  }
  hasErrors() {
    const ctrls = this.props.controls;
    return Object.keys(ctrls).some(
      k => ctrls[k].validationErrors && ctrls[k].validationErrors.length > 0);
  }
  renderErrorMessage() {
    // Returns an error message as a node if any errors are in the store
    const errors = [];
    if ( !this.props || this.props.controls ) return; 
    for (const controlName in this.props.controls) {
      const control = this.props.controls[controlName];
      if (control.validationErrors && control.validationErrors.length > 0) {
        errors.push(
          <div key={controlName}>
            <strong>{`[ ${control.label} ] `}</strong>
            {control.validationErrors.join('. ')}
          </div>,
        );
      }
    }
    let errorMessage;
    if (errors.length > 0) {
      errorMessage = (
        <div style={{ textAlign: 'left' }}>{errors}</div>
      );
    }
    return errorMessage;
  }
  renderChartContainer() {
    return (
      <ChartContainer
        actions={this.props.actions}
        height={this.state.height}
      />
    );
     
  }

  renderPanelContainer(){
     return (
            <ControlPanelsContainer
              actions={this.props.actions}
              form_data={this.props.form_data}
              inj_form_data={this.state.inj_form_data}
              datasource_type={this.props.datasource_type}
              onQuery={this.onQuery}
              onSave={this.toggleModal}
              onStop={this.onStop}
              loading={this.props.chartStatus}
              renderErrorMessage={this.renderErrorMessage}
              {...this.props}
            />
      );
  }

  renderDashboardContainer(){
      return (
             <DashboardViewPage
                 //this will work, but cause to frequent rendering 
                 {...this.props}
                 //queryUpdate={this.queryUpdate}
             />
      );
  }

  render() {
    //if (this.props.standalone) {
    //  return this.renderChartContainer();
    //}
    console.log('simpleflow/components/SimpleflowViewContainer.jsx', this.props, this.state, this.props.inj_form_data);
    if ( this.props.render_container){ 
     switch(this.props.render_container){
       case 'panel': 
                   return this.renderPanelContainer();
                   break;
       case 'chart':
                   return this.renderChartContainer();
                   break;
       case 'dashboard': 
                   return this.renderDashboardContainer();
                   break;
       default: 
                   //return this.renderAllContainers(); 
                   break;
     }
    }

    return (
      <div
        id="simpleflow-container"
        className="container-fluid"
        style={{
          height: this.state.height,
          overflow: 'hidden',
        }}
      >
        <div className="row">
          <div className="col-sm-4">
            <div>
             {
               this.renderPanelContainer()
             }
            </div>
            <div>
            {//
            //<QueryAndSaveBtns
            //  canAdd="True"
            //  onQuery={this.onQuery.bind(this)}
            //  onSave={this.toggleModal.bind(this)}
            //  onStop={this.onStop.bind(this)}
            //  loading={this.props.chartStatus === 'loading'}
            //  errorMessage={this.renderErrorMessage()}
            ///>
            }
            </div>
          </div>
          <div className="col-sm-4">
             {
               this.renderChartContainer()
             }
          </div>
          <div className="col-sm-4">
             <DashboardViewPage 
                 //this will work, but cause to frequent rendering 
                 {...this.props} 
                 //queryUpdate={this.queryUpdate}
             />
          </div>
        </div>
        {this.state.showModal &&
         <SaveModal
          onHide={this.toggleModal.bind(this)}
          actions={this.props.actions}
          form_data={this.props.form_data}
         />
        }

      </div>
    );
  }
}

SimpleflowViewContainer.propTypes = propTypes;

function mapStateToProps(state) {
  const form_data = getFormDataFromControls(state.controls);
  return {
    chartStatus: state.chartStatus,
    datasource_type: state.datasource_type,
    controls: state.controls,
    form_data,
    standalone: state.standalone,
    triggerQuery: state.triggerQuery,
    forcedHeight: state.forced_height,
    queryRequest: state.queryRequest,
    ////inject form data
    inj_form_data: state.inj_form_data,
    render_container: state.render_container,
  };
}

function mapDispatchToProps(dispatch) {
  return {
    actions: bindActionCreators(actions, dispatch),
  };
}

export { SimpleflowViewContainer };
export default connect(mapStateToProps, mapDispatchToProps)(SimpleflowViewContainer);
