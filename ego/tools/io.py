"""
This file contains the eGo main class as well as input & output functions
of eGo in order to build the eGo application container.

"""

__copyright__ = ("Europa-Universität Flensburg, "
                 "Centre for Sustainable Energy Systems")
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke,maltesc"

import sys
import os
import logging
logger = logging.getLogger('ego')

if not 'READTHEDOCS' in os.environ:
    import pyproj as proj
    import geopandas as gpd
    import pandas as pd
    import numpy as np
    from shapely.geometry import Polygon, Point, MultiPolygon
    from sqlalchemy import MetaData, create_engine,  and_, func
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.automap import automap_base
    from geoalchemy2 import *
    from egoio.tools import db
    from etrago.tools.plot import (plot_line_loading, plot_stacked_gen,
                                   curtailment, gen_dist, storage_distribution,
                                   plot_voltage, plot_residual_load
                                   )
    from tools.results import (create_etrago_results)
    from tools.storages import (total_storage_charges, etrago_storages)
    from tools.economics import (etrago_operating_costs, etrago_grid_investment,
                                 edisgo_grid_investment, investment_costs,
                                 get_generator_investment)
    from tools.utilities import get_scenario_setting, get_time_steps
    from etrago.appl import etrago
    from egoio.db_tables.model_draft import RenpassGisParameterRegion
    from egoio.db_tables import model_draft, grid


class egoBasic(object):
    """The eGo basic class creates based on your scenario_setting.json file
    the ...


    Parameters
    ----------
    jsonpath : json
        Path to _scenario_setting.json_ file.

    Results
    -------
    eTraGo : pandas.DataFrame of PyPSA
        Network container of eTraGo based on PyPSA
    eDisGo : pandas.DataFrame of PyPSA
        Network container of eDisGo based on PyPSA
    json_file : dict
        Dict of the scenario_setting.json
    session : sqlalchemy
        Database session for the oedb connection.

    """

    def __init__(self,
                 jsonpath, * args, **kwargs):  # eTraGo=None

        self.jsonpath = 'scenario_setting.json'
        self.json_file = get_scenario_setting(self.jsonpath)

        # self.etrago_network = None
        self.edisgo_network = None

        # Database connection from json_file
        try:
            conn = db.connection(section=self.json_file['global']['db'])
            Session = sessionmaker(bind=conn)
            self.session = Session()
            logger.info('Connected to Database')
        except:
            logger.error('Failed connection to Database',  exc_info=True)

        # get scn_name
        self.scn_name = self.json_file['eTraGo']['scn_name']

        if self.json_file['global']['eTraGo'] is True:
            logger.info('Create eTraGo network')
            self.etrago_network = etrago(self.json_file['eTraGo'])

        if self.json_file['global']['eDisGo'] is True:
            logger.info('Create eDisGo network')
            self.edisgo_network = None  # add eDisGo initialisation here

        pass

    def __repr__(self):

        r = ('eGoResults is created.')
        if not self.etrago_network:
            r += "\nThe results does not incluede eTraGo results"
        if not self.edisgo_network:
            r += "\nThe results does not incluede eDisGo results"
        return r

    pass


class eTraGoResults(egoBasic):
    """eTraGo Results

    This module contains all results of eTraGo for eGo.


    Examples
    --------

    The module can be used by ``etg = eTraGoResults()``

    See also
    --------
    The `eTraGo`_ documentation.

    References
    ----------
    .. _eTraGo:
        `eTraGo <http://etrago.readthedocs.io/en/latest/api/etrago.html>`_, \
        eTraGo Documentation.
    """

    def __init__(self, jsonpath, *args, **kwargs):
        """
        """
        super(eTraGoResults, self).__init__(self, jsonpath,
                                            *args, **kwargs)

        # add selected results to Results container
        self.etrago = pd.DataFrame()
        self.etrago.generator = pd.DataFrame()
        self.etrago.storage_charges = total_storage_charges(self.etrago_network)
        self.etrago.storage_costs = etrago_storages(self.etrago_network)
        self.etrago.operating_costs = etrago_operating_costs(
            self.etrago_network)
        self.etrago.generator = create_etrago_results(self.etrago_network,
                                                      self.scn_name)
        # add functions direct
        #self.etrago_network.etrago_line_loading = etrago_line_loading

        pass

    # include eTraGo functions and methods
    def etrago_line_loading(self, **kwargs):
        """
        Integrate and use function from eTraGo.
        For more information see:
        """
        return plot_line_loading(network=self.etrago_network, **kwargs)

    def etrago_stacked_gen(self, **kwargs):
        """
        Integrate function from eTraGo.
        For more information see:
        """
        return plot_stacked_gen(network=self.etrago_network, **kwargs)

    # def etrago_curtailment(self, **kwargs):
    #    """
    #    Integrate function from eTraGo.
    #    For more information see:
    #    """
    #    return curtailment(network=self.etrago_network, **kwargs)

    def etrago_gen_dist(self, **kwargs):
        """
        Integrate function from eTraGo.
        For more information see:
        """
        return gen_dist(network=self.etrago_network, **kwargs)

    def etrago_storage_distribution(self, **kwargs):
        """
        Integrate function from eTraGo.
        For more information see:
        """
        return storage_distribution(network=self.etrago_network, **kwargs)

    def etrago_voltage(self, **kwargs):
        """
        Integrate function from eTraGo.
        For more information see:
        """
        return plot_voltage(network=self.etrago_network, **kwargs)

    def etrago_residual_load(self, **kwargs):
        """
        Integrate function from eTraGo.
        For more information see:
        """
        return plot_residual_load(network=self.etrago_network, **kwargs)

    # add other methods from eTraGo here


class eDisGoResults(egoBasic):
    """ eDisGo Results

    This module contains all results of eDisGo for eGo.

    ToDo
    ----
    - add eDisGo
    - add iteration for multiple ding0 grids

    """

    def __init__(self, jsonpath, *args, **kwargs):
        super(eDisGoResults, self).__init__(self, jsonpath, *args, **kwargs)

        self.edisgo = pd.DataFrame()

        pass


class eGo(eTraGoResults, eDisGoResults):
    """Main eGo module which including all results and main functionalities.


    Parameters
    ----------
    eTraGo : Network

    eDisGo : Network

    ToDo
    ----
    - add eDisGo
    """

    def __init__(self, jsonpath, *args, **kwargs):
        super(eGo, self).__init__(self, jsonpath,
                                  *args, **kwargs)

        # super().__init__(eDisGo)
        self.total = pd.DataFrame()
        # add total results here

        # add all ego function
        pass

    # write_results_to_db():
    logging.info('Initialisation of eGo Results')


def geolocation_buses(network, session):
    """
    Use Geometries of buses x/y (lon/lat) and Polygons
    of Countries from RenpassGisParameterRegion
    in order to locate the buses

    Parameters
    ----------
    network : Network
        eTraGo Network
    session : sqlalchemy
        session to oedb

    ToDo
    ----
     - check eTrago stack generation plots and other in order of adaptation

    """
    # Start db connetion
    # get renpassG!S scenario data

    meta = MetaData()
    meta.bind = session.bind
    conn = meta.bind
    # get db table
    meta.reflect(bind=conn, schema='model_draft',
                 only=['renpass_gis_parameter_region'])

    # map to classes
    Base = automap_base(metadata=meta)
    Base.prepare()
    RenpassGISRegion = Base.classes.renpass_gis_parameter_region

    # Define regions
    region_id = ['DE', 'DK', 'FR', 'BE', 'LU',
                 'NO', 'PL', 'CH', 'CZ', 'SE', 'NL']

    query = session.query(RenpassGISRegion.gid, RenpassGISRegion.u_region_id,
                          RenpassGISRegion.stat_level, RenpassGISRegion.geom,
                          RenpassGISRegion.geom_point)

    # get regions by query and filter
    Regions = [(gid, u_region_id, stat_level, shape.to_shape(geom),
                shape.to_shape(geom_point)) for gid, u_region_id, stat_level,
               geom, geom_point in query.filter(RenpassGISRegion.u_region_id.
                                                in_(region_id)).all()]

    crs = {'init': 'epsg:4326'}
    # transform lon lat to shapely Points and create GeoDataFrame
    points = [Point(xy) for xy in zip(network.buses.x,  network.buses.y)]
    bus = gpd.GeoDataFrame(network.buses, crs=crs, geometry=points)
    # Transform Countries Polygons as Regions
    region = pd.DataFrame(
        Regions, columns=['id', 'country', 'stat_level', 'Polygon', 'Point'])
    re = gpd.GeoDataFrame(region, crs=crs, geometry=region['Polygon'])
    # join regions and buses by geometry which intersects
    busC = gpd.sjoin(bus, re, how='inner', op='intersects')
    # busC
    # Drop non used columns
    busC = busC.drop(['index_right', 'Point', 'id', 'Polygon',
                      'stat_level', 'geometry'], axis=1)
    # add busC to eTraGo.buses
    network.buses['country_code'] = busC['country']

    # close session
    session.close()

    return network


def results_to_excel(results):
    """
    Wirte results to excel

    """
    # Write the results as xlsx file
    # ToDo add time of calculation to file name
    # add xlsxwriter to setup
    writer = pd.ExcelWriter('open_ego_results.xlsx', engine='xlsxwriter')

    # write results of installed Capacity by fuels
    results.total.to_excel(writer, index=False, sheet_name='Total Calculation')

    # write orgininal data in second sheet
    results.to_excel(writer, index=True, sheet_name='Results by carriers')
    # add plots

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    # buses


def etrago_from_oedb(session, args):
    """
    Function with import eTraGo results for the Database.

    Parameters
    ----------
    session (obj):
        sqlalchemy session to the OEDB

    args (dict):
        args from eGo scenario_setting.json

    ToDo
    ----
        add Mapping for grid schema
        make it more generic -> class?
    """
    result_id = args['global']['result_id']

    # modules from model_draft
    from egoio.db_tables.model_draft import EgoGridPfHvSource as Source,\
        EgoGridPfHvTempResolution as TempResolution
    from etrago.tools.io import loadcfg
    from importlib import import_module
    import pypsa
    import re
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # functions
    def map_ormclass(name):
        """
        Function to map sqlalchemy classes
        """
        try:
            _mapped[name] = getattr(_pkg, _prefix + name)

        except AttributeError:
            print('Warning: Relation %s does not exist.' % name)

        return _mapped

    def dataframe_results(name, session, result_id, ormclass):
        """
        Function to get pandas DataFrames by the result_id
        """

        query = session.query(ormclass).filter(ormclass.result_id == result_id)

        if name == 'Transformer':
            name = 'Trafo'

        df = pd.read_sql(query.statement,
                         session.bind,
                         index_col=name.lower() + '_id')

        if str(ormclass)[:-2].endswith('T'):
            df = pd.Dataframe()

        return df

    def series_results(name, column, session, meta_args, result_id, ormclass):
        """
        Function to get Time Series as pandas DataFrames by the result_id

        ToDo
        ----
        - check index of bus_t and soon is wrong!

        """
        # TODO: pls make more robust
        id_column = re.findall(r'[A-Z][^A-Z]*', name)[0] + '_' + 'id'
        id_column = id_column.lower()

        query = session.query(
            getattr(ormclass, id_column),
            getattr(ormclass, column).
            label(column)).filter(and_(
                ormclass.result_id == result_id
            ))

        df = pd.io.sql.read_sql(query.statement,
                                session.bind,
                                columns=[column],
                                index_col=id_column)

        df.index = df.index.astype(str)

        # change of format to fit pypsa
        df = df[column].apply(pd.Series).transpose()

        try:
            assert not df.empty
            df.index = timeindex
        except AssertionError:
            print("No data for %s in column %s." % (name, column))

        return df

    # create config for results
    path = os.getcwd()
    # add meta_args with args of results
    config = loadcfg(path+'/tools/config.json')['results']

    # map and Database settings of etrago_from_oedb()
    _prefix = 'EgoGridPfHvResult'
    schema = 'model_draft'
    packagename = 'egoio.db_tables'
    _pkg = import_module(packagename + '.' + schema)
    temp_ormclass = 'TempResolution'
    carr_ormclass = 'Source'
    _mapped = {}

    # get metadata
    version = args['global']['gridversion']

    orm_meta = getattr(_pkg, _prefix + 'Meta')

    # check result_id

    result_id_in = session.query(orm_meta.result_id).filter(orm_meta.
                                                            result_id == result_id).all()
    if result_id_in:
        logger.info('Choosen result_id %s found in DB', result_id)
    else:
        logger.info('Error: result_id not found in DB')

    # get meta data as args
    meta = session.query(orm_meta.result_id, orm_meta.scn_name, orm_meta.calc_date,
                         orm_meta.user_name, orm_meta.method, orm_meta.start_snapshot,
                         orm_meta.end_snapshot, orm_meta.solver, orm_meta.settings
                         ).filter(orm_meta.result_id == result_id)

    meta_df = pd.read_sql(
        meta.statement, meta.session.bind, index_col='result_id')

    meta_args = dict(meta_df.settings[result_id])
    meta_args['scn_name'] = meta_df.scn_name[result_id]
    meta_args['method'] = meta_df.method[result_id]
    meta_args['start_snapshot'] = meta_df.start_snapshot[result_id]
    meta_args['end_snapshot'] = meta_df.end_snapshot[result_id]
    meta_args['solver'] = meta_df.solver[result_id]

    # get TempResolution
    temp = TempResolution

    tr = session.query(temp.temp_id, temp.timesteps,
                       temp.resolution, temp.start_time).one()

    timeindex = pd.DatetimeIndex(start=tr.start_time,
                                 periods=tr.timesteps,
                                 freq=tr.resolution)

    timeindex = timeindex[meta_args['start_snapshot'] -
                          1: meta_args['end_snapshot']]

    meta_args['temp_id'] = tr.temp_id

    # create df for PyPSA network

    network = pypsa.Network()
    network.set_snapshots(timeindex)

    timevarying_override = False

    if pypsa.__version__ == '0.11.0':
        old_to_new_name = {'Generator':
                           {'p_min_pu_fixed': 'p_min_pu',
                            'p_max_pu_fixed': 'p_max_pu',
                            'source': 'carrier',
                            'dispatch': 'former_dispatch'},
                           'Bus':
                           {'current_type': 'carrier'},
                           'Transformer':
                           {'trafo_id': 'transformer_id'},
                           'Storage':
                           {'p_min_pu_fixed': 'p_min_pu',
                            'p_max_pu_fixed': 'p_max_pu',
                            'soc_cyclic': 'cyclic_state_of_charge',
                            'soc_initial': 'state_of_charge_initial',
                            'source': 'carrier'}}

        timevarying_override = True

    else:
        old_to_new_name = {'Storage':
                           {'soc_cyclic': 'cyclic_state_of_charge',
                            'soc_initial': 'state_of_charge_initial'}}

    # get data into dataframes
    logger.info('Start building eTraGo results network')
    for comp, comp_t_dict in config.items():

        orm_dict = map_ormclass(comp)

        pypsa_comp_name = 'StorageUnit' if comp == 'Storage' else comp
        ormclass = orm_dict[comp]

        if not comp_t_dict:
            df = dataframe_results(comp, session, result_id, ormclass)

            if comp in old_to_new_name:
                tmp = old_to_new_name[comp]
                df.rename(columns=tmp, inplace=True)

            network.import_components_from_dataframe(df, pypsa_comp_name)

        if comp_t_dict:

            for name, columns in comp_t_dict.items():

                name = name[:-1]
                pypsa_comp_name = name

                if name == 'Storage':
                    pypsa_comp_name = 'StorageUnit'
                if name == 'Transformer':
                    name = 'Trafo'

                for col in columns:

                    df_series = series_results(
                        name, col, session, meta_args, result_id, ormclass)

                    # TODO: VMagPuSet?
                    if timevarying_override and comp == 'Generator':
                        idx = df[df.former_dispatch == 'flexible'].index
                        idx = [i for i in idx if i in df_series.columns]
                        df_series.drop(idx, axis=1, inplace=True)

                    try:

                        pypsa.io.import_series_from_dataframe(
                            network,
                            df_series,
                            pypsa_comp_name,
                            col)

                    except (ValueError, AttributeError):
                        print("Series %s of component %s could not be "
                              "imported" % (col, pypsa_comp_name))

    print('Done')
    logger.info('Imported eTraGo results of id = %s ', result_id)
    return network


if __name__ == '__main__':
    pass
