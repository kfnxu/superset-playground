/* eslint camelcase: 0 */
import React from 'react';
import ReactDOM from 'react-dom';
import { createStore, applyMiddleware, compose } from 'redux';
import { Provider } from 'react-redux';
import thunk from 'redux-thunk';

import { now } from '../modules/dates';
import { initEnhancer } from '../reduxUtils';
import AlertsWrapper from '../components/AlertsWrapper';
import { getControlsState, getFormDataFromControls } from './stores/store';
import { initJQueryAjax } from '../modules/utils';
import SimpleflowViewContainer from './components/SimpleflowViewContainer';
import { simpleflowReducer } from './reducers/simpleflowReducer';
import { appSetup } from '../common';
import './main.css';


export default class SimpleflowViewPage extends React.Component{

  constructor(props) {
    super(props);
    appSetup();
    initJQueryAjax();
  }

  componentWillMount() {
  }

  componentDidMount() {
  }

  render() {

    const simpleflowViewContainer = document.getElementById('js-simpleflow-view-container');
    const bootstrapData = JSON.parse(simpleflowViewContainer.getAttribute('data-bootstrap'));
    const controls = getControlsState(bootstrapData, bootstrapData.form_data);
    //
    const render_container = bootstrapData.form_data['render_container'] ?bootstrapData.form_data['render_container'] : "all"; 
    delete bootstrapData.form_data;
    console.log('javascripts/simpleflow/index.jsx', bootstrapData, render_container);

    // Initial state
    const bootstrappedState = Object.assign(
    bootstrapData, {
    chartStatus: null,
    chartUpdateEndTime: null,
    chartUpdateStartTime: now(),
    dashboards: [],
    controls,
    latestQueryFormData: getFormDataFromControls(controls),
    filterColumnOpts: [],
    isDatasourceMetaLoading: false,
    isStarred: false,
    queryResponse: null,
    triggerQuery: true,
    triggerRender: false,
    alert: null,
    render_container: render_container,
    },
    );

    const store = createStore(simpleflowReducer, bootstrappedState,
      compose(applyMiddleware(thunk), initEnhancer(false)),
    );


     return (
     <Provider store={store}>
       <div>
        <SimpleflowViewContainer />
        <AlertsWrapper />
       </div>
     </Provider>
     );
  }
}


