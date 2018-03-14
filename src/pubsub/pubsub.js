//https://github.com/yguan/local-pub-sub
/*
The MIT License (MIT)

Copyright (c) 2015 Yong Guan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

!function(e){if("object"==typeof exports)module.exports=e();else if("function"==typeof define&&define.amd)define(e);else{var f;"undefined"!=typeof window?f=window:"undefined"!=typeof global?f=global:"undefined"!=typeof self&&(f=self),f.localPubSub=e()}}(function(){var define,module,exports;return (function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);throw new Error("Cannot find module '"+o+"'")}var f=n[o]={exports:{}};t[o][0].call(f.exports,function(e){var n=t[o][1][e];return s(n?n:e)},f,f.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(_dereq_,module,exports){
/*jslint nomen: true*/
/*global module,require,localStorage,window */

var pubSub = _dereq_('micro-pubsub').create();
var storageKeyPrefix = 'LocalPubSub-';
var storageKeyPrefixLength = storageKeyPrefix.length;

function convertToStorageKey(topic) {
    return storageKeyPrefix + topic;
}

function convertToTopic(storageKey) {
    if (!storageKey) {
        return '';
    }
    return storageKey.slice(storageKeyPrefixLength);
}

function bind(el, eventType, handler) {
    if (el.addEventListener) {
        el.addEventListener(eventType, handler, false);
    } else if (el.attachEvent) {
        el.attachEvent('on' + eventType, handler);
    }
}

bind(window, 'storage', function (event) {
    var key = event.key;
    var newValue = event.newValue;
    var topic = convertToTopic(key);

    if (topic !== '' && newValue !== null) {
        pubSub.publish(topic, JSON.parse(localStorage.getItem(key)));
        localStorage.removeItem(key);
    }
});

module.exports = {
    subscribe: function (topic, listener) {
        pubSub.subscribe(topic, listener);
    },
    unsubscribe: function (topic) {
        pubSub.unsubscribe(topic);
    },
    publish: function (topic, info) {
        localStorage.setItem(convertToStorageKey(topic), JSON.stringify(info));
    }
};
},{"micro-pubsub":2}],2:[function(_dereq_,module,exports){
/*jslint nomen: true*/
/*global module */
// Modified from David Walsh's pubsub. http://davidwalsh.name/pubsub-javascript

var PubSub = function () {
    this.topics = {};
};

PubSub.prototype.subscribe = function(topic, listener) {
    var me = this;
    console.log('PubSub.prototype.subscribe topic, listener', topic, listener);
    // Create the topic's object if not yet created
    if(!me.topics.hasOwnProperty(topic)){
        me.topics[topic] = [];
    }

    // Add the listener to queue
    me.topics[topic].push(listener);
    console.log('PubSub.prototype.subscribe me.topics', me.topics);
};

PubSub.prototype.unsubscribe = function(topic) {
    delete this.topics[topic];
};

PubSub.prototype.publish = function(topic, info) {
    var me = this;

    console.log('PubSub.prototype.publish topic, info', topic, info);
    // If the topic doesn't exist, or there's no listeners in queue, just leave
    if(!me.topics.hasOwnProperty(topic)){
        return;
    }

    // Cycle through topics queue, fire!
    me.topics[topic].forEach(function(listener) {
        listener(info != undefined ? info : {});
    });
    console.log('PubSub.prototype.publish me.topics', me.topics);
};

module.exports = {
    create: function() {
        return new PubSub();
    }
};
},{}]},{},[1])
(1)
});
