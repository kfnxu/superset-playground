# superset-playground

* goal: make control-panel to update chart on other tab of the browser.
* what: looks like this one: ![result](/images/pubsub.png) <!-- .element height="30%" width="30%" -->
* why: to make superset supports multi-iframes.
* how: use pub/sub model for the data communication between control-panel and chart-container.

```javascript
superset/templates/superset/basic.html
<script src="/static/assets/public/js/pubsub.js"></script>
[pubsub.js](/src/pubsub/pubsub.js)

assets/javascripts/integrationoffice/components/controls/SelectControl.jsx
  onChange(opt) {
    let optionValue = opt ? opt.value : null;
    // if multi, return options values as an array
    if (this.props.multi) {
      optionValue = opt ? opt.map(o => o.value) : null;
    }
    this.props.onChange(optionValue);
    this.props.onChangePanel(optionValue);
    //use pub/sub
    localPubSub.publish('SelectControl', { name: this.props.name, value:optionValue});
  }

superset/assets/javascripts/integrationoffice/components/IntegrationofficeViewContainer.jsx
  componentDidMount() {
    console.log('IntegrationofficeViewContainer componentDidMount');
    if (!this.props.standalone) {
      this.props.actions.fetchDatasources();
    }
    window.addEventListener('resize', this.handleResize.bind(this));
    this.triggerQueryIfNeeded();
    var self = this;
    //subscribe the SelectControl pub
    localPubSub.subscribe('SelectControl', function (obj) {
       console.log("localPubSub.subscribe('SelectControl'", obj);
       self.props.actions.setControlValue(obj.name, obj.value, []);
       self.props.actions.resetControls();
       self.props.actions.triggerQuery();
    });
  }

