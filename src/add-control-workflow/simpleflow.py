"""This module contains the "Viz" internal simpleflow plugin objects

These plugin objects represent the backend of all the visualizations that
Superset can render for simpleflow
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy
import hashlib
import logging
import traceback
import uuid
import zlib

from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from flask import request
from flask_babel import lazy_gettext as _
from markdown import markdown
import simplejson as json
from six import string_types, PY3
from dateutil import relativedelta as rdelta

from superset import app, utils, cache
from superset.utils import DTTM_ALIAS

## BaseViz is abstrat class
##from superset.viz_base import Viz, viz_types_list
from superset.viz import Viz

##

from superset.graph import (
    BaseGraph
)

config = app.config
stats_logger = config.get('STATS_LOGGER')

### todo. use naming convension, such as prefix all simpleflow controls name to 'sf_'
mask_json = '{"model_group":"model_id","sex_group":"sex_id","age_select":"age_group_id","location":"location_id", "cause":"cause_id", "risk":"risk_id"}'
form_data_db_mask = json.loads(mask_json)

class SimpleFlowViz(Viz):

    """All simpleflow visualizations derive this base class"""

    viz_type = None
    verbose_name = "Base Viz"
    credits = ""
    is_timeseries = False

    def __init__(self, datasource, form_data):
        if not datasource:
            raise Exception("Viz is missing a datasource")
        self.datasource = datasource
        self.request = request
        self.viz_type = form_data.get("viz_type")
        self.form_data = form_data
        print("from viz_base.py self.viz_type")
        #print(self.viz_type)

        self.query = ""
        self.token = self.form_data.get(
            'token', 'token_' + uuid.uuid4().hex[:8])
        self.metrics = self.form_data.get('metrics') or []
        self.groupby = self.form_data.get('groupby') or []

        self.status = None
        self.error_message = None

        self.baseGraph = BaseGraph()

    def get_df(self, query_obj=None):
        """Returns a pandas dataframe based on the query object"""
        if not query_obj:
            query_obj = self.query_obj()

        ##print('BaseViz')
        #print('baseviz return query_obj', query_obj)

        self.error_msg = ""
        self.results = None

        timestamp_format = None
        if self.datasource.type == 'table':
            dttm_col = self.datasource.get_col(query_obj['granularity'])
            if dttm_col:
                timestamp_format = dttm_col.python_date_format

        # The datasource here can be different backend but the interface is common
        self.results = self.datasource.query(query_obj)
        print('plugins/internal/simpleflow.py get_df self.results, self.results.df', self.results, self.results.df )

        self.query = self.results.query
        self.status = self.results.status
        self.error_message = self.results.error_message

        df = self.results.df
        # Transform the timestamp we received from database to pandas supported
        # datetime format. If no python_date_format is specified, the pattern will
        # be considered as the default ISO date format
        # If the datetime format is unix, the parse will use the corresponding
        # parsing logic.
        if df is None or df.empty:
            self.status = utils.QueryStatus.FAILED
            if not self.error_message:
                self.error_message = "No data."
            return pd.DataFrame()
        else:
            if DTTM_ALIAS in df.columns:
                if timestamp_format in ("epoch_s", "epoch_ms"):
                    df[DTTM_ALIAS] = pd.to_datetime(df[DTTM_ALIAS], utc=False)
                else:
                    df[DTTM_ALIAS] = pd.to_datetime(
                        df[DTTM_ALIAS], utc=False, format=timestamp_format)
                if self.datasource.offset:
                    df[DTTM_ALIAS] += timedelta(hours=self.datasource.offset)
            df.replace([np.inf, -np.inf], np.nan)
            df = df.fillna(0)
        return df

    def get_extra_filters(self):
        extra_filters = self.form_data.get('extra_filters', [])
        return {f['col']: f['val'] for f in extra_filters}

    def query_obj(self):
        """Building a query object"""
        form_data = self.form_data
        groupby = form_data.get("groupby") or []
        metrics = form_data.get("metrics") or []

        # extra_filters are temporary/contextual filters that are external
        # to the slice definition. We use those for dynamic interactive
        # filters like the ones emitted by the "Filter Box" visualization
        extra_filters = self.get_extra_filters()
        granularity = (
            form_data.get("granularity") or form_data.get("granularity_sqla")
        )
        limit = int(form_data.get("limit") or 0)
        timeseries_limit_metric = form_data.get("timeseries_limit_metric")
        row_limit = int(
            form_data.get("row_limit") or config.get("ROW_LIMIT"))

        # __form and __to are special extra_filters that target time
        # boundaries. The rest of extra_filters are simple
        # [column_name in list_of_values]. `__` prefix is there to avoid
        # potential conflicts with column that would be named `from` or `to`
        since = (
            extra_filters.get('__from') or
            form_data.get("since") or
            config.get("SUPERSET_DEFAULT_SINCE", "1 year ago")
        )

        from_dttm = utils.parse_human_datetime(since)
        now = datetime.now()
        if from_dttm > now:
            from_dttm = now - (from_dttm - now)

        until = extra_filters.get('__to') or form_data.get("until", "now")
        to_dttm = utils.parse_human_datetime(until)
        if from_dttm > to_dttm:
            raise Exception("From date cannot be larger than to date")

        # extras are used to query elements specific to a datasource type
        # for instance the extra where clause that applies only to Tables
        extras = {
            'where': form_data.get("where", ''),
            'having': form_data.get("having", ''),
            'having_druid': form_data.get('having_filters') \
                if 'having_filters' in form_data else [],
            'time_grain_sqla': form_data.get("time_grain_sqla", ''),
            'druid_time_origin': form_data.get("druid_time_origin", ''),
        }
        print("baseViz extras")
        ##print(extras)
        #print("query_obj baseViz form_data", form_data);
        #where_filter_str = ""
        ### built the filter for dashboard, since slice is now integrated with dashboard 
        #dashboard_filter_array = []
        #try:
        ##   mask_json = '{"model_group":"model_id","sex_group":"sex_id","age_select":"age_group_id","location":"country_code"}'
        ##   form_data_db_mask = json.loads(mask_json)
        #   where_filter_array = []
        #   for attr, value in form_data.items():
        #    if (form_data_db_mask.get(str(attr), None) is not None) and (value is not None) and value and len(value) > 0 :
        #         where_filter =  form_data_db_mask.get(str(attr)) + " in ( " + ",".join(value) + ")"
        #         where_filter_array.append(where_filter)
        #         ## build the dashboard_filter_array 
        #         dashboard_filter_array += [{
        #            'col': form_data_db_mask.get(str(attr)),
        #            'op': 'in',
        #            'val': value,
        #         }]
        #   if len(where_filter_array) > 0 :
        #     where_filter_str = " and ".join(where_filter_array)
        #   ## sample format: age_group_id in ( 1,2,22) and model_id in ( 46,4,7,10,,108,28,38,94,106) and sex_id in ( 3)
        #   print("viz.py baseViz simpleflow_line where_filter_str, dashboard_filter_array", where_filter_str, dashboard_filter_array)
        #
        #except Exception as e:
        #        logging.exception(e)
        #        print("form_data fields in viz.py is not iterable");

        filters = form_data['filters'] if 'filters' in form_data \
                else []
        for col, vals in self.get_extra_filters().items():
            print("viz.py baseViz looping extra_filters col, vals, self.datasource.filterable_column_names", col, vals, self.datasource.filterable_column_names)
            if not (col and vals) or col.startswith('__'):
                continue
            elif col in self.datasource.filterable_column_names:
                # Quote values with comma to avoid conflict
                filters += [{
                    'col': col,
                    'op': 'in',
                    'val': vals,
                }]
            elif form_data_db_mask.get(col) in self.datasource.filterable_column_names:
                # Quote values with comma to avoid conflict
                filters += [{
                    'col': form_data_db_mask.get(col),
                    'op': 'in',
                    'val': map(int, vals),
                }]

        ##filters.extend(dashboard_filter_array)
        #print('viz.py baseViz query_obj filters', filters, form_data['filters'])
        
        d = {
            'granularity': granularity,
            'from_dttm': from_dttm,
            'to_dttm': to_dttm,
            'is_timeseries': self.is_timeseries,
            'groupby': groupby,
            'metrics': metrics,
            'row_limit': row_limit,
            'filter': filters,
            'timeseries_limit': limit,
            'extras': extras,
            'timeseries_limit_metric': timeseries_limit_metric,
            'form_data': form_data,
        }
        ##print(d)
        return d

    @property
    def cache_timeout(self):
        if self.form_data.get('cache_timeout'):
            return int(self.form_data.get('cache_timeout'))
        if self.datasource.cache_timeout:
            return self.datasource.cache_timeout
        if (
                hasattr(self.datasource, 'database') and
                self.datasource.database.cache_timeout):
            return self.datasource.database.cache_timeout
        return config.get("CACHE_DEFAULT_TIMEOUT")

    def get_json(self, force=False):
        return json.dumps(
            self.get_payload(force),
            default=utils.json_int_dttm_ser, ignore_nan=True)

    @property
    def cache_key(self):
        s = str([(k, self.form_data[k]) for k in sorted(self.form_data.keys())])
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    def get_payload(self, force=False):
        """Handles caching around the json payload retrieval"""
        cache_key = self.cache_key
        payload = None
        force = force if force else self.form_data.get('force') == 'true'
        if not force and cache:
            payload = cache.get(cache_key)

        if payload:
            stats_logger.incr('loaded_from_source')
            is_cached = True
            try:
                cached_data = zlib.decompress(payload)
                if PY3:
                    cached_data = cached_data.decode('utf-8')
                payload = json.loads(cached_data)
            except Exception as e:
                logging.error("Error reading cache: " +
                              utils.error_msg_from_exception(e))
                payload = None
            logging.info("Serving from cache")

        if not payload:
            stats_logger.incr('loaded_from_cache')
            data = None
            is_cached = False
            cache_timeout = self.cache_timeout
            stacktrace = None
            try:
                df = self.get_df()
                if not self.error_message:
                    data = self.get_data(df)
            except Exception as e:
                logging.exception(e)
                if not self.error_message:
                    self.error_message = str(e)
                self.status = utils.QueryStatus.FAILED
                data = None
                stacktrace = traceback.format_exc()
            payload = {
                'cache_key': cache_key,
                'cache_timeout': cache_timeout,
                'data': data,
                'error': self.error_message,
                'form_data': self.form_data,
                'query': self.query,
                'status': self.status,
                'stacktrace': stacktrace,
            }
            payload['cached_dttm'] = datetime.utcnow().isoformat().split('.')[0]
            logging.info("Caching for the next {} seconds".format(
                cache_timeout))
            data = self.json_dumps(payload)
            if PY3:
                data = bytes(data, 'utf-8')
            if cache and self.status != utils.QueryStatus.FAILED:
                try:
                    cache.set(
                        cache_key,
                        zlib.compress(data),
                        timeout=cache_timeout)
                except Exception as e:
                    # cache.set call can fail if the backend is down or if
                    # the key is too large or whatever other reasons
                    logging.warning("Could not cache key {}".format(cache_key))
                    logging.exception(e)
                    cache.delete(cache_key)
        payload['is_cached'] = is_cached
        return payload

    def json_dumps(self, obj):
        return json.dumps(obj, default=utils.json_int_dttm_ser, ignore_nan=True)

    @property
    def data(self):
        """This is the data object serialized to the js layer"""
        content = {
            'form_data': self.form_data,
            'token': self.token,
            'viz_name': self.viz_type,
            'filter_select_enabled': self.datasource.filter_select_enabled,
        }
        return content

    def get_csv(self):
        df = self.get_df()
        include_index = not isinstance(df.index, pd.RangeIndex)
        return df.to_csv(index=include_index, encoding="utf-8")

    def get_data(self, df):
        return []

    @property
    def json_data(self):
        return json.dumps(self.data)


class SimpleFlowTsViz(SimpleFlowViz):

    """A rich line chart component with tons of options"""

    viz_type = "simpleflow_line"
    #viz_type = "line"
    verbose_name = _("Time Series - Line Chart")
    sort_series = False
    is_timeseries = True

    def to_series(self, df, classed='', title_suffix=''):
        print('SimpleFlowTimeSeriesViz to_series df')
        #print(df)
        cols = []
        for col in df.columns:
            if col == '':
                cols.append('N/A')
            elif col is None:
                cols.append('NULL')
            else:
                cols.append(col)
        df.columns = cols
        series = df.to_dict('series')

        chart_data = []
        for name in df.T.index.tolist():
            ys = series[name]
            if df[name].dtype.kind not in "biufc":
                continue
            if isinstance(name, string_types):
                series_title = name
            else:
                name = ["{}".format(s) for s in name]
                if len(self.form_data.get('metrics')) > 1:
                    series_title = ", ".join(name)
                else:
                    series_title = ", ".join(name[1:])
            if title_suffix:
                series_title += title_suffix

            d = {
                "key": series_title,
                "classed": classed,
                "values": [
                    {'x': ds, 'y': ys[ds] if ds in ys else None}
                    for ds in df.index
                ],
            }
            chart_data.append(d)
        return chart_data

    def get_data(self, df):
        fd = self.form_data
        #df = df.fillna(0)
        query_object = self.query_obj()
        df = self.get_df(query_object)
        df = df.fillna(0)

        print("SimpleFlowTimeSeriesViz get_data, df")
        #print(fd)

        if fd.get("granularity") == "all":
            raise Exception("Pick a time granularity for your time series")

        df = df.pivot_table(
            index=DTTM_ALIAS,
            columns=fd.get('groupby'),
            values=fd.get('metrics'))

        fm = fd.get("resample_fillmethod")
        if not fm:
            fm = None
        how = fd.get("resample_how")
        rule = fd.get("resample_rule")
        if how and rule:
            df = df.resample(rule, how=how, fill_method=fm)
            if not fm:
                df = df.fillna(0)

        if self.sort_series:
            dfs = df.sum()
            dfs.sort_values(ascending=False, inplace=True)
            df = df[dfs.index]

        if fd.get("contribution"):
            dft = df.T
            df = (dft / dft.sum()).T

        rolling_periods = fd.get("rolling_periods")
        rolling_type = fd.get("rolling_type")

        if rolling_type in ('mean', 'std', 'sum') and rolling_periods:
            if rolling_type == 'mean':
                df = pd.rolling_mean(df, int(rolling_periods), min_periods=0)
            elif rolling_type == 'std':
                df = pd.rolling_std(df, int(rolling_periods), min_periods=0)
            elif rolling_type == 'sum':
                df = pd.rolling_sum(df, int(rolling_periods), min_periods=0)
        elif rolling_type == 'cumsum':
            df = df.cumsum()

        num_period_compare = fd.get("num_period_compare")
        if num_period_compare:
            num_period_compare = int(num_period_compare)
            prt = fd.get('period_ratio_type')
            if prt and prt == 'growth':
                df = (df / df.shift(num_period_compare)) - 1
            elif prt and prt == 'value':
                df = df - df.shift(num_period_compare)
            else:
                df = df / df.shift(num_period_compare)

            df = df[num_period_compare:]

        chart_data = self.to_series(df)

        time_compare = fd.get('time_compare')
        if time_compare:
            query_object = self.query_obj()
            delta = utils.parse_human_timedelta(time_compare)
            query_object['inner_from_dttm'] = query_object['from_dttm']
            query_object['inner_to_dttm'] = query_object['to_dttm']
            query_object['from_dttm'] -= delta
            query_object['to_dttm'] -= delta

            df2 = self.get_df(query_object)
            df2[DTTM_ALIAS] += delta
            df2 = df2.pivot_table(
                index=DTTM_ALIAS,
                columns=fd.get('groupby'),
                values=fd.get('metrics'))
            chart_data += self.to_series(
                df2, classed='superset', title_suffix="---")
            chart_data = sorted(chart_data, key=lambda x: x['key'])
        return chart_data


    ## overwrite base class's method query_obj
    def query_obj(self):
        """Building a query object"""
        
        form_data = self.form_data
        groupby = form_data.get("groupby") or []
        metrics = form_data.get("metrics") or []

        # extra_filters are temporary/contextual filters that are external
        # to the slice definition. We use those for dynamic interactive
        # filters like the ones emitted by the "Filter Box" visualization
        extra_filters = self.get_extra_filters()
        granularity = (
            form_data.get("granularity") or form_data.get("granularity_sqla")
        )
        limit = int(form_data.get("limit") or 0)
        timeseries_limit_metric = form_data.get("timeseries_limit_metric")
        row_limit = int(
            form_data.get("row_limit") or config.get("ROW_LIMIT"))

        # __form and __to are special extra_filters that target time
        # boundaries. The rest of extra_filters are simple
        # [column_name in list_of_values]. `__` prefix is there to avoid
        # potential conflicts with column that would be named `from` or `to`
        since = (
            extra_filters.get('__from') or
            form_data.get("since") or
            config.get("SUPERSET_DEFAULT_SINCE", "1 year ago")
        )
        from_dttm = utils.parse_human_datetime(since)
        now = datetime.now()
        if from_dttm > now:
            from_dttm = now - (from_dttm - now)

        until = extra_filters.get('__to') or form_data.get("until", "now")
        to_dttm = utils.parse_human_datetime(until)
        if from_dttm > to_dttm:
            raise Exception("From date cannot be larger than to date")

        ## extras are used to query elements specific to a datasource type
        ## for instance the extra where clause that applies only to Tables
        print("plugins/internal/simpleflow.py form_data", form_data);
        where_filter_str = ""
        ## built the filter for dashboard, since slice is now integrated with dashboard 
        dashboard_filter_array = [] 
        try:
           ##mask_json = '{"model_group":"model_id","sex_group":"sex_id","age_select":"age_group_id","location":"country_code"}'
           ##form_data_db_mask = json.loads(mask_json)
           where_filter_array = []
           for attr, value in form_data.items():
            print("plugins/internal/simpleflow.py integrationoffice form_data attr, value", attr, value, form_data_db_mask.get(str(attr), None))
            if (form_data_db_mask.get(str(attr), None) is not None) and (value is not None) and value and not any(isinstance(sublist, list) for sublist in value) and len(value) > 0 :
                 where_filter =  form_data_db_mask.get(str(attr)) + " in ( " + ",".join(value) + ")"
                 where_filter_array.append(where_filter)
                 ## build the dashboard_filter_array 
                 dashboard_filter_array += [{
                    'col': form_data_db_mask.get(str(attr)),
                    'op': 'in',
                    'val': map(int, value),
                 }]
           if len(where_filter_array) > 0 :
             where_filter_str = " and ".join(where_filter_array)
           ## sample format: age_group_id in ( 1,2,22) and model_id in ( 46,4,7,10,,108,28,38,94,106) and sex_id in ( 3)
           print("plugins/internal/simpleflow.py where_filter_str, dashboard_filter_array", dashboard_filter_array, where_filter_str)
          
        except Exception as e:
                logging.exception(e)
                print("plugins/internal/simpleflow.py exception form_data fields in viz.py is not iterable");

        default_form_data_json = '{"resample_fillmethod": null, "show_brush": false, "line_interpolation": "linear", "show_legend": true, "filters": [], "granularity_sqla": "year", "rolling_type": "null", "show_markers": false, "since": "100 years ago", "time_compare": null, "until": "5057", "resample_rule": null, "period_ratio_type": "growth", "metrics": ["avg__model_id", "avg__rt_mean"], "timeseries_limit_metric": null, "resample_how": null, "slice_id": 177, "num_period_compare": "", "viz_type_superset": "table", "level_group": "1", "groupby": ["model_name"], "rich_tooltip": true, "limit": 5000, "datasource": "108__table", "x_axis_showminmax": true, "contribution": false, "time_grain_sqla": "Time Column"}'
        default_form_data = json.loads(default_form_data_json)
        form_data.update(default_form_data)
        #print("plugins/internal/simpleflow.py form_data", form_data, default_form_data)
        extras = {
            #'where': form_data.get("where", ''),
            'where': where_filter_str,
            'having': form_data.get("having", ''),
            'having_druid': form_data.get('having_filters') \
                if 'having_filters' in form_data else [],
            'time_grain_sqla': form_data.get("time_grain_sqla", ''),
            'druid_time_origin': form_data.get("druid_time_origin", ''),
        }
        #print(extras)
        filters = [] 
        #filters = form_data['filters'] if 'filters' in form_data \
        #        else []
        #for col, vals in self.get_extra_filters().items():
        #    if not (col and vals) or col.startswith('__'):
        #        continue
        #    elif col in self.datasource.filterable_column_names:
        #        # Quote values with comma to avoid conflict
        #        filters += [{
        #            'col': col,
        #            'op': 'in',
        #            'val': vals,
        #        }]
        ## sample format: [{u'col': u'country_code', u'val': [u'ALB', u'DZA', u'ASM', u'ADO', u'ATG'], u'op': u'in'}]
        filters.extend(dashboard_filter_array)
        print('plugins/internal/simpleflow.py simpleflow_line query_obj filters', filters, dashboard_filter_array, form_data['filters'])

        #data-set for controlSetRows
        vis_container_id = form_data.get("viscontainer_group", 1)
        vis_id = form_data.get("vistype_group", 1)
        viz_type_form = form_data.get("viz_type",1)
        search_setting = self.baseGraph.get_search_setting_graph_db(viz_type_form, vis_container_id, vis_id)
        #build setting array
        panel = {}
        sections = []
        rows = []
        row = []
        section_name_index = 1
        row_name_index = 2 
        control_name_index = 3

        if len(search_setting) > 0:
          section_name = search_setting[0][section_name_index]
          row_name = search_setting[0][row_name_index]
          counter = 0
          for r in search_setting:
           ### new rows, search_setting has to have ordered by section_name
           if section_name != r[section_name_index] :
              sections.append({"label": section_name,"description": section_name, "controlSetRows":rows})
              section_name = r[section_name_index] 
              rows = []
               
           row.append(r[control_name_index])
           rows.append(row)
           row = []
        ### append the last section
        sections.append({"label": section_name,"description": section_name, "controlSetRows":rows})

        form_data['search_dependencies_controlSections'] =  sections

        ##rebuild form_data for data from graph-db
        search_categories = self.baseGraph.get_search_categories_graph_db(viz_type_form, vis_container_id, vis_id)
        search_categories_array = []
        ###clear all form_data related to setting, can be more effecient 
        ###
        for r in search_categories:
        #    if r[2] != 'model_version' :
             if form_data_db_mask.get(str(r[2]), None) is None:
                form_data[r[2]] = []

        for r in search_categories:
            name = r[2]
            #print('search_categories, r, name', r, name)
            #todo name all to 'sf_'
            #if r[2] == 'model_version' or r[2] == 'cause' or r[2] == 'risk' : 
            if form_data_db_mask.get(str(r[2]), None) is not None:
               name = 'sf_' + r[2]
            if name not in form_data or type(form_data[name]) is not list: 
               form_data[name] = [] 
            form_data[name].append([r[0],r[1]])
            a = { "ID": r[0], "NAME": r[1], "CAT": r[2] }
            search_categories_array.append(a)

        #attach graph data to form_data 
        form_data['graph_search_categories'] = search_categories_array;

        ###
        ### like to keep these example code which shows how the control-sections
        ### control-rows and controls are formated in the frontend to generate 
        ### controlpancel inputs
        ###
        ##data-set for controlSetRows
        #controlSections = []
        #controlSetRows = []
        #controlSetRows.append(["viz_type"])
        #controlSetRows.append(["viscontainer_group"])
        #controlSetRows.append(["vistype_group"])
        #controlSetRows.append(["measure"])
        #controlSetRows.append(["cause"])
        #controlSetRows.append(["risk"])
        #controlSetRows.append(["age_select"])
        #controlSetRows.append(["location"])
        #controlSetRows.append(["model_group"])
        ##controlSetRows.append(["metrics"])
        ##controlSetRows.append(["groupby"])
        ##controlSetRows.append(["limit", "timeseries_limit_metric"])
        #section = {
        #    'label': 'section 1', 
        #    'description': 'descrition 1', 
        #    'controlSetRows': controlSetRows,
        #}
        #controlSections.append(section)

        #controlSetRows = []
        #controlSetRows.append(["rate_of_change_switch"])
        #controlSetRows.append(["year_group"])
        #controlSetRows.append(["level_group"])
        #controlSetRows.append(["sex_group"])
        #controlSetRows.append(["unit_group"])
        ##controlSetRows.append(["show_brush", "show_legend"])
        ##controlSetRows.append( ["rich_tooltip"])
        ##controlSetRows.append(["show_markers", "x_axis_showminmax"])
        ##controlSetRows.append(["line_interpolation", "contribution"])
        #section = {
        #    'label': 'section 2',
        #    'description': 'descrition 2',
        #    'controlSetRows': controlSetRows,
        #}
        #controlSections.append(section)

        ##controlSetRows = []
        ##controlSetRows.append(["rolling_type", "rolling_periods"])
        ##controlSetRows.append(["time_compare"])
        ##controlSetRows.append(["num_period_compare", "period_ratio_type"])
        ##controlSetRows.append(["resample_how", "resample_rule"])
        ##controlSetRows.append(["resample_fillmethod"])
        ##section = {
        ##    'label': 'section 3',
        ##    'description': 'descrition 3',
        ##    'controlSetRows': controlSetRows,
        ##}
        ##controlSections.append(section)
        #form_data['search_dependencies_controlSections'] =  controlSections
        ##print('form_data')
        ##print(form_data)

        #end of

        d = {
            'granularity': granularity,
            'from_dttm': from_dttm,
            'to_dttm': to_dttm,
            'is_timeseries': self.is_timeseries,
            'groupby': groupby,
            'metrics': metrics,
            'row_limit': row_limit,
            'filter': filters,
            'timeseries_limit': limit,
            'extras': extras,
            'timeseries_limit_metric': timeseries_limit_metric,
            'form_data': form_data,
        }
        #print(d)
        return d


class SimpleflowTsMultiChartViz(SimpleFlowTsViz):

    """A multichart """

    viz_type = "simpleflow_multichart"
    sort_series = False 
    verbose_name = _("MultiChart")
    #is_timeseries = True
    is_timeseries = False

    # overite parent query_obj
    def query_obj(self):
        """Building a query object"""
        form_data = self.form_data
        groupby = form_data.get("groupby") or []
        #groupby = []
        metrics = form_data.get("metrics") or []

        # extra_filters are temporary/contextual filters that are external
        # to the slice definition. We use those for dynamic interactive
        # filters like the ones emitted by the "Filter Box" visualization
        extra_filters = self.get_extra_filters()
        granularity = (
            form_data.get("granularity") or form_data.get("granularity_sqla")
        )
        limit = int(form_data.get("limit") or 0)
        #timeseries_limit_metric = form_data.get("timeseries_limit_metric")
        row_limit = int(
            form_data.get("row_limit") or config.get("ROW_LIMIT"))

        ## __form and __to are special extra_filters that target time
        ## boundaries. The rest of extra_filters are simple
        ## [column_name in list_of_values]. `__` prefix is there to avoid
        ## potential conflicts with column that would be named `from` or `to`
        since = (
            extra_filters.get('__from') or
            form_data.get("since") or
            config.get("SUPERSET_DEFAULT_SINCE", "1 year ago")
        )

        from_dttm = utils.parse_human_datetime(since)
        now = datetime.now()
        if from_dttm > now:
            from_dttm = now - (from_dttm - now)
        until = extra_filters.get('__to') or form_data.get("until", "now")
        to_dttm = utils.parse_human_datetime(until)
        if from_dttm > to_dttm:
            raise Exception("From date cannot be larger than to date")

        ## extras are used to query elements specific to a datasource type
        ## for instance the extra where clause that applies only to Tables
        extras = {
            #'where': form_data.get("where", ''),
            'having': form_data.get("having", ''),
            'having_druid': form_data.get('having_filters') \
                if 'having_filters' in form_data else [],
            'time_grain_sqla': form_data.get("time_grain_sqla", ''),
            'druid_time_origin': form_data.get("druid_time_origin", ''),
        }

        filters = form_data['filters'] if 'filters' in form_data \
                else []
        for col, vals in self.get_extra_filters().items():
            if not (col and vals) or col.startswith('__'):
                continue
            elif col in self.datasource.filterable_column_names:
                # Quote values with comma to avoid conflict
                filters += [{
                    'col': col,
                    'op': 'in',
                    'val': vals,
                }]
        d = {
            'granularity': granularity,
            'from_dttm': from_dttm,
            'to_dttm': to_dttm,
            'is_timeseries': self.is_timeseries,
            'groupby': groupby,
            'metrics': metrics,
            'row_limit': row_limit,
            'filter': filters,
            #'timeseries_limit': limit,
            'extras': extras,
            #'timeseries_limit_metric': timeseries_limit_metric,
            'form_data': form_data,
        }
        #print('NVD3MultiChartViz query_obj')
        #print(d)

        return d

    def to_series(self, df, classed='', title_suffix=''):

        # todo change to format to sequence rather than column-name:
        # column-0 is x
        # column-1 is y
        # column-2 is type-id
        # column-4 is yAxis
        # column-3 is name-id
        # for this setting, df.columns[2] is 'avg__plot_name_id'
        # gb = df.groupby('avg__plot_name_id', sort=True)
        #print('NVD3MultiChartViz to_series --df, columns')
        #print(df) 
        #print(df.columns)
        #gb = df.groupby(df.columns[1]) 
        gb = df.groupby('plot_name_id')
        chart_data = [] 
       
        for name, group in gb:
            #print('--group')
            #print(name)
            #print(group)
            values = []
            plot_type_id = ''
            # index is column-0 which is x
            for index, row in group.iterrows():
                  #print('--index')
                  #print(index)
                  if ( plot_type_id == '' ):
                       #plot_type_id = row[df.columns[2]]
                       plot_type_id = row['plot_type_id'] 
                  size = 1
                  height = 1
                  std = 0
                  #for backward support
                  if 'avg__x_std' in row:
                       size = row['avg__x_std']
                  if 'avg__y_std' in row:
                       height = row['avg__y_std']
                  #new format for diff
                  if 'avg__x_diff' in row:
                       size = row['avg__x_diff']
                  if 'avg__y_diff' in row:
                       height = row['avg__y_diff']
                  if 'avg__std' in row:
                       std = row['avg__std']
                  v = { 
                         "x": row['__timestamp'],
                         "y":row['avg__y'],
                         "size": size,
                         "height": height,
                         #"shape":"cross",
                         "shape":"dpoint",
                         "std": std,  
                       }
                  #print('shape dataset')
                  #print(v)
                  values.append(v)
            #print('--value')
            #print(values)
            plot_type = 'line'
            if ( plot_type_id == 1 ):
                 plot_type = 'scatter'
            elif ( plot_type_id == 2 ):
                 plot_type = 'line'
            elif ( plot_type_id == 3 ):
                 plot_type = 'area'
            elif ( plot_type_id == 4 ):
                 plot_type = 'bar'
            else: 
                 plot_type = 'scatter'

            d = {
                "key": name,
                "classed": classed,
                "values": values,
                #added for multichart,
                "yAxis": 1,
                "type": plot_type,

            }
            chart_data.append(d)

        return chart_data

    def get_data(self, df):
        #print('NVD3MultiChartViz get_data df, form_data')
        fd = self.form_data
        #print(df)

        chart_data = self.to_series(df)

        time_compare = fd.get('time_compare')
        if time_compare:
            query_object = self.query_obj()
            delta = utils.parse_human_timedelta(time_compare)
            query_object['inner_from_dttm'] = query_object['from_dttm']
            query_object['inner_to_dttm'] = query_object['to_dttm']
            query_object['from_dttm'] -= delta
            query_object['to_dttm'] -= delta

            df2 = self.get_df(query_object)
            df2[DTTM_ALIAS] += delta
            df2 = df2.pivot_table(
                index=DTTM_ALIAS,
                columns=fd.get('groupby'),
                values=fd.get('metrics'))
            chart_data += self.to_series(
                df2, classed='superset', title_suffix="---")
            chart_data = sorted(chart_data, key=lambda x: x['key'])
        return chart_data

class SimpleFlowTsBarViz(SimpleFlowTsViz):

    """A bar chart where the x axis is time"""

    #viz_type = "bar"
    viz_type = "simpleflow_bar"
    sort_series = True
    verbose_name = _("Time Series - Bar Chart")

class SimpleFlowTsCompareViz(SimpleFlowTsViz):

    """A line chart component where you can compare the % change over time"""

    #viz_type = 'compare'
    viz_type = 'simpleflow_compare'
    verbose_name = _("Time Series - Percent Change")

class SimpleFlowTsStackedViz(SimpleFlowTsViz):

    """A rich stack area chart"""

    #viz_type = "area"
    viz_type = "simpleflow_area"
    verbose_name = _("Time Series - Stacked")
    sort_series = True

class IHMEChoroplethViz(SimpleFlowTsViz):

    """A rich stack area chart"""

    viz_type = "ihme_choropleth"
    verbose_name = _("Choropleth Map")
    sort_series = True
    # overite parent query_obj
    def query_obj(self):
        """Building a query object"""

        form_data = self.form_data
        groupby = form_data.get("groupby") or []
        metrics = form_data.get("metrics") or []

        # extra_filters are temporary/contextual filters that are external
        # to the slice definition. We use those for dynamic interactive
        # filters like the ones emitted by the "Filter Box" visualization
        extra_filters = self.get_extra_filters()
        granularity = (
            form_data.get("granularity") or form_data.get("granularity_sqla")
        )
        limit = int(form_data.get("limit") or 0)
        timeseries_limit_metric = form_data.get("timeseries_limit_metric")
        row_limit = int(
            form_data.get("row_limit") or config.get("ROW_LIMIT"))

        # __form and __to are special extra_filters that target time
        # boundaries. The rest of extra_filters are simple
        # [column_name in list_of_values]. `__` prefix is there to avoid
        # potential conflicts with column that would be named `from` or `to`
        since = (
            extra_filters.get('__from') or
            form_data.get("since") or
            config.get("SUPERSET_DEFAULT_SINCE", "1 year ago")
        )

        from_dttm = utils.parse_human_datetime(since)
        now = datetime.now()
        if from_dttm > now:
            from_dttm = now - (from_dttm - now)

        until = extra_filters.get('__to') or form_data.get("until", "now")
        to_dttm = utils.parse_human_datetime(until)
        if from_dttm > to_dttm:
            raise Exception("From date cannot be larger than to date")

        ## extras are used to query elements specific to a datasource type
        ## for instance the extra where clause that applies only to Tables
        where_filter_str = ""
        ## built the filter for dashboard, since slice is now integrated with dashboard 
        dashboard_filter_array = []
        try:
           ##mask_json = '{"model_group":"model_id","sex_group":"sex_id","age_select":"age_group_id","location":"country_code"}'
           ##form_data_db_mask = json.loads(mask_json)
           where_filter_array = []
           for attr, value in form_data.items():
            #print("plugins/internal/simpleflow.py IHMEChoroplethViz looking at form_data.items() attr, value", attr, value)
            ## conditions getting too long, rewrite following codes 
            ## 'not any(isinstance(sublist, list) for sublist in value)' is to check if 'value' is [[]], which also means
            ## there is no selected items. and no need to get all those items, if no selected item, then all will be selected. 
            if (form_data_db_mask.get(str(attr), None) is not None) and (value is not None) and value and not any(isinstance(sublist, list) for sublist in value) and len(value) > 0 :
                 where_filter =  form_data_db_mask.get(str(attr)) + " in ( " + ",".join(value) + ")"
                 where_filter_array.append(where_filter)
                 ## build the dashboard_filter_array 
                 dashboard_filter_array += [{
                    'col': form_data_db_mask.get(str(attr)),
                    'op': 'in',
                    'val': map(int, value),
                 }]
           if len(where_filter_array) > 0 :
             where_filter_str = " and ".join(where_filter_array)
           ## sample format: age_group_id in ( 1,2,22) and model_id in ( 46,4,7,10,,108,28,38,94,106) and sex_id in ( 3)
           print("plugins/internal/simpleflow.py IHMEChoroplethViz form_data, where_filter_str, dashbbard_filter_array", form_data, dashboard_filter_array, where_filter_str)
        except Exception as e:
                logging.exception(e)
                print("plugins/internal/simpleflow.py IHMEChoroplethViz exception form_data fields in viz.py is not iterable");

        ### between inheriented class, only this setting is different, may merge into one
        default_form_data_json = '{"resample_fillmethod": null, "show_brush": false, "line_interpolation": "linear", "show_legend": true, "filters": [], "granularity_sqla": "year", "rolling_type": "null", "show_markers": false, "since": "100 years ago", "time_compare": null, "until": "5057", "resample_rule": null, "period_ratio_type": "growth", "metrics": ["avg__model_id", "avg__rt_mean", "avg__location_id","avg__year"], "timeseries_limit_metric": null, "resample_how": null, "slice_id": 177, "num_period_compare": "", "viz_type_superset": "table", "level_group": "1", "groupby": ["id"], "rich_tooltip": true, "limit": 5000, "datasource": "108__table", "x_axis_showminmax": true, "contribution": false, "time_grain_sqla": "Time Column"}'
        default_form_data = json.loads(default_form_data_json)
        #print("plugins/internal/simpleflow.py IHMEChoroplethViz form_data before update", form_data);
        form_data.update(default_form_data)
        #print("plugins/internal/simpleflow.py IHMEChoroplethViz form_data", form_data, default_form_data)
        extras = {
            #'where': form_data.get("where", ''),
            'where': where_filter_str,
            'having': form_data.get("having", ''),
            'having_druid': form_data.get('having_filters') \
                if 'having_filters' in form_data else [],
            'time_grain_sqla': form_data.get("time_grain_sqla", ''),
            'druid_time_origin': form_data.get("druid_time_origin", ''),
        }
        #print(extras)
        filters = []
        filters.extend(dashboard_filter_array)
        print('plugins/internal/simpleflow.py ihme_choropleth query_obj filters', dashboard_filter_array, filters, form_data['filters'])

        #data-set for controlSetRows
        vis_container_id = form_data.get("viscontainer_group", 1)
        vis_id = form_data.get("vistype_group", 1)
        viz_type_form = form_data.get("viz_type",1)
        search_setting = self.baseGraph.get_search_setting_graph_db(viz_type_form, vis_container_id, vis_id)
        #build setting array
        panel = {}
        sections = []
        rows = []
        row = []
        section_name_index = 1
        row_name_index = 2
        control_name_index = 3

        if len(search_setting) > 0:
          section_name = search_setting[0][section_name_index]
          row_name = search_setting[0][row_name_index]
          counter = 0
          for r in search_setting:
           ### new rows, search_setting has to have ordered by section_name
           if section_name != r[section_name_index] :
              sections.append({"label": section_name,"description": section_name, "controlSetRows":rows})
              section_name = r[section_name_index]
              rows = []

           row.append(r[control_name_index])
           rows.append(row)
           row = []
        ### append the last section
        sections.append({"label": section_name,"description": section_name, "controlSetRows":rows})
        form_data['search_dependencies_controlSections'] =  sections

        ##rebuild form_data for data from graph-db
        search_categories = self.baseGraph.get_search_categories_graph_db(viz_type_form, vis_container_id, vis_id)
        search_categories_array = []
        ###clear all form_data related to setting, can be more effecient 
        for r in search_categories:
            #if r[2] != 'model_version':
            if form_data_db_mask.get(str(r[2]), None) is None:
               form_data[r[2]] = [] 

        for r in search_categories:
            name = r[2]
            #print('search_categories, r, name', r, name)
            #if r[2] == 'model_version' or r[2] == 'cause' or r[2] == 'risk' :                 
            if form_data_db_mask.get(str(r[2]), None) is not None:
               name = 'sf_' + r[2]
            if name not in form_data or type(form_data[name]) is not list:
               form_data[name] = []
            ### need to cleanup the format data, otherwise may add duplicated format data
            #print("plugins/internal/simpleflow.py form_data", name, form_data[name])
            form_data[name].append([r[0],r[1]])
            #print("plugins/internal/simpleflow.py form_data append", name, form_data[name])
            a = { "ID": r[0], "NAME": r[1], "CAT": r[2] }
            search_categories_array.append(a)

        #attach graph data to form_data 
        form_data['graph_search_categories'] = search_categories_array;
        d = {
            'granularity': granularity,
            'from_dttm': from_dttm,
            'to_dttm': to_dttm,
            'is_timeseries': self.is_timeseries,
            'groupby': groupby,
            'metrics': metrics,
            'row_limit': row_limit,
            'filter': filters,
            'timeseries_limit': limit,
            'extras': extras,
            'timeseries_limit_metric': timeseries_limit_metric,
            'form_data': form_data,
        }
        #print(d)
        return d


    def get_payload(self, force=False):
        """Handles caching around the json payload retrieval"""
        cache_key = self.cache_key
        payload = None
        force = force if force else self.form_data.get('force') == 'true'
        if not force and cache:
            payload = cache.get(cache_key)

        if payload:
            stats_logger.incr('loaded_from_source')
            is_cached = True
            try:
                cached_data = zlib.decompress(payload)
                if PY3:
                    cached_data = cached_data.decode('utf-8')
                payload = json.loads(cached_data)
            except Exception as e:
                logging.error("Error reading cache: " +
                              utils.error_msg_from_exception(e))
                payload = None
            logging.info("Serving from cache")
        if not payload:
            stats_logger.incr('loaded_from_cache')
            data = None
            is_cached = False
            cache_timeout = self.cache_timeout
            stacktrace = None
            try:
                df = self.get_df()
                if not self.error_message:
                    data = self.get_data(df)
                #df = None
                #data = self.get_data(df)
            except Exception as e:
                logging.exception(e)
                if not self.error_message:
                    self.error_message = str(e)
                self.status = utils.QueryStatus.FAILED
                data = None
                stacktrace = traceback.format_exc()
            payload = {
                'cache_key': cache_key,
                'cache_timeout': cache_timeout,
                'data': data,
                'error': self.error_message,
                'form_data': self.form_data,
                'query': self.query,
                'status': self.status,
                'stacktrace': stacktrace,
            }
            #print('plugins/internal/simpleflow.py IHMEChoroplethViz payload, data', payload, data);
            payload['cached_dttm'] = datetime.utcnow().isoformat().split('.')[0]
            logging.info("Caching for the next {} seconds".format(
                cache_timeout))
            data = self.json_dumps(payload)
            if PY3:
                data = bytes(data, 'utf-8')
            if cache and self.status != utils.QueryStatus.FAILED:
                try:
                    cache.set(
                        cache_key,
                        zlib.compress(data),
                        timeout=cache_timeout)
                except Exception as e:
                    # cache.set call can fail if the backend is down or if
                    # the key is too large or whatever other reasons
                    logging.warning("Could not cache key {}".format(cache_key))
                    logging.exception(e)
                    cache.delete(cache_key)
        payload['is_cached'] = is_cached
        return payload

    def get_data(self, df):
        query_object = self.query_obj()
        df = self.get_df(query_object)
        df = df.fillna(0)
        chart_data = self.to_series(df)
        return chart_data

    def to_series(self, df, classed='', title_suffix=''):
        chart_data = []
        for index, row in df.iterrows():
             #print("IHMEChoroplethViz to_series iterrows index, row", index, row, row.to_dict(), df.columns)
             d = { 
                   "id": str(index+1), 
                   "mean": row['avg__rt_mean']*100, # x100 to show color on map,  
                   "year_id": int(row['avg__year']), #row['__timestamp'], #need to change to 'year'
                   "loc_id": str(int(row['avg__location_id']))
                 }
             chart_data.append(d)
        #print("IHMEChoroplethViz to_series columns ", dir(df.columns))
        #for index, member  in enumerate(df.columns.tolist()):
        #     print("IHMEChoroplethViz to_series columns ", index, member, df.columns[index])
            
        ###builds five columns needed for choropleth map dataset
        #IHMEChoroplethViz get_data columns  0 model_name model_name
        #IHMEChoroplethViz get_data columns  1 __timestamp __timestamp
        #IHMEChoroplethViz get_data columns  2 avg__model_id avg__model_id
        #IHMEChoroplethViz get_data columns  3 avg__rt_mean avg__rt_mean
        #IHMEChoroplethViz get_data columns  4 avg__location_id avg__location_id
        return chart_data

