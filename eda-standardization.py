#!/usr/bin/env python
# coding: utf-8

# In[61]:


import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import math
import osmnx as ox
from shapely.ops import unary_union
import contextily as cx
from summarytools import dfSummary
import ipywidgets as widgets
from IPython.display import display
import uuid
import pycountry
import os


# In[2]:


# from google.colab import data_table


# In[3]:


fetch_data = False


# ## Get country boundaries

# In[4]:


un_boundaries = gpd.read_file("https://zstagigaprodeuw1.blob.core.windows.net/gigainframapkit-public-container/country_boundary_data/boundaries.geojson")
algeria = un_boundaries[un_boundaries.romnam == "Algeria"]


# In[5]:


algeria.plot()


# In[6]:


algeria_boundary = algeria.total_bounds
algeria_utm = algeria.estimate_utm_crs()
algeria_latitude = algeria.centroid.y.squeeze()


# In[57]:


def get_iso3_country_code(country_name):
    try:
        country = pycountry.countries.get(name=country_name)
        return country.alpha_3
    except AttributeError:
        return None


# In[59]:


algeria_iso3 = get_iso3_country_code("Algeria")
print(f"The ISO3 code for Algeria is {algeria_iso3}")


# ## Get point of interest (POI) data

# In[7]:


if fetch_data:
    place = "Algeria"
    tags = {"amenity": "school"}
    algeria_schools_gdf = ox.features_from_place(place, tags)
else:
    algeria_schools_gdf = gpd.read_file("https://zstagigaprodeuw1.blob.core.windows.net/gigainframapkit-public-container/algeria/algeria-schools.geojson")


# In[8]:


algeria_schools_gdf = algeria_schools_gdf[["osmid","amenity","element_type","addr:city","isced:level","operator", "geometry"]]


# ## Get Ookla data

# In[9]:


def get_perf_tiles_parquet_url(service: str, year: int, quarter: int) -> str:
    quarter_start = f"{year}-{(((quarter - 1) * 3) + 1):02}-01"
    url = f"s3://ookla-open-data/parquet/performance/type={service}/year={year}/quarter={quarter}/{quarter_start}_performance_{service}_tiles.parquet"
    return url


# ### Mobile

# In[10]:


if fetch_data:
    mobile_perf_tiles_url = get_perf_tiles_parquet_url("mobile", 2024, 2)
    bbox_filters = [('tile_y', '<=', algeria_boundary[3]), ('tile_y', '>=', algeria_boundary[1]),
                ('tile_x', '<=', algeria_boundary[2]), ('tile_x', '>=', algeria_boundary[0])]
    mobile_tiles_df = pd.read_parquet(mobile_perf_tiles_url,
                           filters=bbox_filters,
                           columns=['tile_x', 'tile_y', 'tests', 'avg_d_kbps', 'avg_lat_ms'],
                           storage_options={"s3": {"anon": True}}
                           )
else:
    mobile_tiles_df = pd.read_csv("https://zstagigaprodeuw1.blob.core.windows.net/gigainframapkit-public-container/algeria/algeria-ookla-mobile-tiles.csv",index_col=0)


# In[11]:


mobile_tiles_gdf = gpd.GeoDataFrame(mobile_tiles_df, geometry=gpd.points_from_xy(mobile_tiles_df.tile_x, mobile_tiles_df.tile_y), crs="EPSG:4326").drop(columns=["tile_x", "tile_y"])


# #### Generate mobile coverage area

# In[12]:


tile_size_at_latitude=610.8*np.cos(math.radians(algeria_latitude))
buffers = mobile_tiles_gdf.to_crs(algeria_utm).buffer(tile_size_at_latitude).to_crs("EPSG:4326")
single_polygon = unary_union(buffers)
algeria_mobile_coverage_gdf = gpd.GeoDataFrame(geometry=[single_polygon], crs="EPSG:4326")


# ### Fixed

# In[13]:


if fetch_data:
    fixed_perf_tiles_url = get_perf_tiles_parquet_url("fixed", 2024, 2)
    fixed_tiles_df = pd.read_parquet(fixed_perf_tiles_url,
                           filters=bbox_filters,
                           columns=['tile_x', 'tile_y', 'tests', 'avg_d_kbps', 'avg_lat_ms'],
                           storage_options={"s3": {"anon": True}}
                           )
else:
    fixed_tiles_df = pd.read_csv("https://zstagigaprodeuw1.blob.core.windows.net/gigainframapkit-public-container/algeria/algeria-ookla-fixed-tiles.csv")


# ## Get cell site data

# In[14]:


algeria_cell_sites = pd.read_csv("https://zstagigaprodeuw1.blob.core.windows.net/gigainframapkit-public-container/algeria/algeria-cell-sites.csv")


# In[15]:


algeria_cell_sites_gdf = gpd.GeoDataFrame(algeria_cell_sites, geometry=gpd.points_from_xy(algeria_cell_sites.lon, algeria_cell_sites.lat), crs="EPSG:4326").drop(columns=["lon", "lat"])


# ## Get transmission node data

# In[16]:


algeria_nodes = pd.read_csv("https://zstagigaprodeuw1.blob.core.windows.net/gigainframapkit-public-container/algeria/algeria-transmission-nodes.csv")


# In[17]:


algeria_nodes_gdf = gpd.GeoDataFrame(algeria_nodes, geometry=gpd.points_from_xy(algeria_nodes.lon, algeria_nodes.lat), crs="EPSG:4326").drop(columns=["lon", "lat"])


# # Tabular data analysis

# ## Point of interest (POI) data

# In[18]:


# data_table.DataTable(algeria_schools_gdf, num_rows_per_page=10)


# In[19]:


dfSummary(algeria_schools_gdf)


# ## Cell site data

# In[20]:


# data_table.DataTable(algeria_cell_sites_gdf, num_rows_per_page=10)


# In[21]:


dfSummary(algeria_cell_sites_gdf)


# ## Transmission node data

# In[22]:


# data_table.DataTable(algeria_nodes_gdf, num_rows_per_page=10)


# In[23]:


dfSummary(algeria_nodes_gdf)


# # Geographical analysis

# In[24]:


colors = {"schools": "#e41a1c", "cell_sites": "#377eb8", "nodes": "#ff7f00"}


# In[25]:


def plot_points(points_gdf, title="Map", color="red", point_size=20):
    """
    Plot a generic geodataframe with a basemap
    
    Parameters:
    gdf : GeoDataFrame with any geometry type
    title : str, plot title
    point_color : str, color for points/polygons (hex code or name)
    point_size : int, size of markers (for points only)
    """
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Plot points
    points_gdf.plot(
            ax=ax,
            color=color,
            markersize=point_size,
            alpha=0.7,
            edgecolor='black',
            linewidth=0.5
        )
    
    # Add basemap
    cx.add_basemap(
        ax, crs=points_gdf.crs)
    
    # Style the plot
    plt.title(title, pad=20, fontsize=16)
    ax.axis('off')
    
    # Add a text box with feature count
    stats_text = f'Total Features: {len(points_gdf)}'
    ax.text(
        0.02, 0.02, stats_text,
        transform=ax.transAxes,
        bbox=dict(facecolor='white', alpha=0.7),
        fontsize=12
    )
    plt.tight_layout()
    plt.show()


# In[26]:


def plot_outside_points(points_gdf, boundary_gdf, title="Points Outside Boundary", color="red", point_size=20):    
    # Find points inside and outside
    points_inside = gpd.sjoin(points_gdf, boundary_gdf, predicate='within', how='inner')
    points_outside = points_gdf[~points_gdf.index.isin(points_inside.index)]
    
    # Create plot and zoom to outside points
    fig, ax = plt.subplots(figsize=(10, 10))
    points_outside = points_outside.to_crs(epsg=4326)
    
    # Set map bounds with different buffers for lat/lon
    if len(points_outside) > 0:
        minx, miny, maxx, maxy = points_outside.total_bounds
        avg_lat = (miny + maxy) / 2
        x_buffer = 0.5 / np.cos(np.deg2rad(avg_lat))
        y_buffer = 0.5
        ax.set_xlim(minx - x_buffer, maxx + x_buffer)
        ax.set_ylim(miny - y_buffer, maxy + y_buffer)
    
    # Plot points
    points_outside.plot(ax=ax, color=color, markersize=point_size, edgecolor='black', linewidth=0.5)
    
    # Manually create a legend
    legend_elements = [Patch(facecolor=color, edgecolor='black', label='Outside')]
    ax.legend(handles=legend_elements)
    
    # Set title and axis off
    ax.set_title(f"{title}\nOutside points: {len(points_outside)}")
    ax.axis('off')
    
    # Add basemap
    cx.add_basemap(ax, crs=points_outside.crs)

    # Add a text box with the total feature count
    stats_text = f'Total Features: {len(points_outside)}'
    ax.text(
        0.02, 0.02, stats_text,
        transform=ax.transAxes,
        bbox=dict(facecolor='white', alpha=0.7),
        fontsize=12
    )
    plt.tight_layout()
    plt.show()


# In[27]:


def show_plots_with_widgets(points_gdf, boundary_gdf, fig1_title="Points", fig2_title="Points outside boundaries", color="red"):
    # Create tab widget
    tab = widgets.Tab()
    
    # Create output widgets for each plot
    out1 = widgets.Output()
    out2 = widgets.Output()
    
    # Set tab contents
    tab.children = [out1, out2]
    
    # Set tab titles
    tab.set_title(0, fig1_title)
    tab.set_title(1, fig2_title)
    
    # Display plots in respective tabs
    with out1:
        plot_points(points_gdf, title=fig1_title, color=color)
    with out2:
        plot_outside_points(points_gdf, boundary_gdf, title=fig2_title, color=color)
    
    display(tab)


# ## Point of interest (POI) data

# In[28]:


algeria_schools_gdf.geometry.type.value_counts()


# In[29]:


algeria_schools_gdf.geometry = algeria_schools_gdf.geometry.centroid


# In[30]:


show_plots_with_widgets(algeria_schools_gdf, algeria, "Schools", "Schools outside Algeria", color=colors["schools"])


# ## Cell site data

# In[31]:


algeria_cell_sites_gdf.geometry.type.value_counts()


# In[32]:


show_plots_with_widgets(algeria_cell_sites_gdf, algeria, "Cell Sites", "Cell Sites outside Algeria", color=colors["cell_sites"])


# ## Transmission node data

# In[33]:


algeria_nodes_gdf.geometry.type.value_counts()


# In[34]:


show_plots_with_widgets(algeria_nodes_gdf, algeria, "Transmission Nodes", "Transmission Nodes outside Algeria", color=colors["nodes"])


# ## Mobile coverage

# In[35]:


def plot_coverage(gdf, title="Mobile Coverage", fill_color="#3498db", alpha=0.3):
    """
    Plot coverage polygons with a basemap
    Parameters:
    gdf : GeoDataFrame with polygon geometry
    title : str, plot title
    fill_color : str, color for polygons (hex code or name)
    alpha : float, transparency level (0 to 1)
    """
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Plot the geodataframe
    gdf.plot(
        ax=ax,
        color=fill_color,
        alpha=alpha,
        edgecolor='white',
        linewidth=0.5
    )
    
    # Add basemap
    cx.add_basemap(
        ax, 
        crs=gdf.crs,
        source=cx.providers.CartoDB.DarkMatter
    )
    
    # Style the plot
    plt.title(title, pad=20, fontsize=16)
    ax.axis('off')
    
    # Add a text box with coverage area count
    stats_text = f'Coverage Areas: {len(gdf)}'
    plt.figtext(
        0.02, 0.02, stats_text,
        bbox=dict(facecolor='white', alpha=0.7),
        fontsize=12
    )
    
    plt.tight_layout()
    plt.show()


# In[36]:


def clip_coverage(coverage_gdf, boundary_gdf):
    """
    Clip coverage polygons to boundary and optionally show before/after plots
    
    Parameters:
    coverage_gdf : GeoDataFrame with coverage polygons
    boundary_gdf : GeoDataFrame with country boundary
    
    Returns:
    GeoDataFrame with clipped coverage polygons
    """
    # Ensure same CRS
    if coverage_gdf.crs != boundary_gdf.crs:
        coverage_gdf = coverage_gdf.to_crs(boundary_gdf.crs)
    
    # Perform the clip operation
    clipped_coverage = gpd.clip(coverage_gdf, boundary_gdf)
    
    return clipped_coverage


# In[37]:


def show_coverage_plots_with_widgets(coverage_gdf, boundary_gdf, fig1_title="Coverage", fig2_title="Clipped Coverage"):
    # Create tab widget
    tab = widgets.Tab()
    
    # Create output widgets for each plot
    out1 = widgets.Output()
    out2 = widgets.Output()
    
    # Set tab contents
    tab.children = [out1, out2]
    
    # Set tab titles
    tab.set_title(0, fig1_title)
    tab.set_title(1, fig2_title)
    
    # Display plots in respective tabs
    with out1:
        plot_coverage(coverage_gdf, title=fig1_title)
    with out2:
        clipped_coverage = clip_coverage(coverage_gdf, boundary_gdf)
        plot_coverage(clipped_coverage, title=fig2_title)
    
    display(tab)


# In[38]:


algeria_clipped_mobile_coverage_gdf = clip_coverage(algeria_mobile_coverage_gdf, algeria)


# In[39]:


show_coverage_plots_with_widgets(algeria_mobile_coverage_gdf, algeria, "Mobile Coverage", "Clipped Mobile Coverage")


# # Standardize data

# In[40]:


def extract_lat_lon(gdf, id_column='id'):
   """
   Create a new dataframe with latitude, longitude and UUID columns
   """
   df = pd.DataFrame({
       id_column: [str(uuid.uuid4()) for _ in range(len(gdf))],
       'dataset_id': str(uuid.uuid4()),
       'lat': gdf.geometry.y,
       'lon': gdf.geometry.x
   })
   return df


# In[ ]:


current_directory = os.getcwd()
data_directory = os.path.join(current_directory, "data", algeria_iso3, "processed")
os.makedirs(data_directory, exist_ok=True)


# ## Point of interest (POI) data

# In[41]:


poi_metadata = pd.DataFrame({
   'column_name': ['poi_id', 'dataset_id', 'lat', 'lon', 'poi_type', 'is_public', 'poi_subtype', 'country_code', 'is_connected', 'connectivity_type'],
   'column_type': ['UUID', 'UUID', 'float', 'float', 'string', 'boolean', 'string', 'string', 'boolean', 'string'],
   'levels': [''] * 10,
   'example': ['123e4567-e89b-12d3-a456-426614174000', '987fcdeb-51a2-12d3-a456-426614174000', '36.7538', '3.0588', 'school', 'True', 'primary school', 'DZA', 'True', '4G'],
   'mandatory': ['Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'Yes', 'No', 'No'],
   'definition': [
       'Unique identifier for the POI',
       'Unique identifier for the dataset',
       'Latitude coordinate',
       'Longitude coordinate',
       'Type of point of interest',
       'Whether the POI is public or private',
       'Specific subtype of the POI',
       'ISO 3166-1 alpha-3 country code',
       'Whether the POI has connectivity',
       'Type of internet connectivity'
   ]
})
styled_df = poi_metadata.style.set_properties(**{
   'text-align': 'left',
   'border': '1px solid black',
   'padding': '8px'
}).set_table_styles([
   {'selector': 'thead', 'props': [('background-color', '#f2f2f2'), ('font-weight', 'bold'), ('border-bottom', '2px solid black')]},
   {'selector': 'tbody tr:nth-of-type(odd)', 'props': [('background-color', '#f9f9f9')]}
])
display(styled_df)


# In[42]:


# Create blank dataframe with id, latitute and longitude columns
formatted_algeria_schools = extract_lat_lon(algeria_schools_gdf, id_column='poi_id')

# Fill in other columns
formatted_algeria_schools["country_code"] = algeria_iso3
formatted_algeria_schools["poi_type"] = "school"
formatted_algeria_schools["is_connected"] = False


# In[43]:


formatted_algeria_schools.head()
# data_table.DataTable(formatted_algeria_schools, num_rows_per_page=10)


# In[67]:


formatted_algeria_schools.to_csv(os.path.join(data_directory, "formatted_algeria_schools.csv"), index=False)


# ## Cell site data

# In[44]:


cell_metadata = pd.DataFrame({
   'column_name': ['ict_id', 'dataset_id', 'latitude', 'longitude', 'operator_name', 'radio_type', 'antenna_height_m', 'backhaul_type', 'backhaul_throughput_mbps'],
   'column_type': ['UUID', 'UUID', 'float', 'float', 'string', 'string', 'float', 'string', 'float'],
   'levels': [
       '',  # ict_id
       '',  # dataset_id
       '',  # latitude
       '',  # longitude
       '',  # operator_name
       'LTE, UMTS, GSM, CDMA',  # radio_type
       '',  # antenna_height_m
       'fiber, microwave, satellite',  # backhaul_type
       ''   # backhaul_throughput_mbps
   ],
   'example': ['123e4567-e89b-12d3-a456-426614174000', '987fcdeb-51a2-12d3-a456-426614174000', '38.988755', '1.401938', 'TelOperator', 'LTE', '25', 'fiber', '1000'],
   'mandatory': ['Yes', 'Yes', 'Yes', 'Yes', 'No', 'Yes', 'Yes', 'No', 'No'],
   'definition': [
       'Cell tower identifier',
       'Unique identifier for the dataset',
       'Cell tower geographical latitude',
       'Cell tower geographical longitude',
       'Mobile network operator name',
       'Type of radio transmission technology',
       'Antenna height on the tower or building',
       'Type of backhaul connectivity of the cell tower',
       'Equipped throughput of the backhaul'
   ]
})
styled_df = cell_metadata.style.set_properties(**{
   'text-align': 'left',
   'border': '1px solid black',
   'padding': '8px'
}).set_table_styles([
   {'selector': 'thead', 'props': [('background-color', '#f2f2f2'), ('font-weight', 'bold'), ('border-bottom', '2px solid black')]},
   {'selector': 'tbody tr:nth-of-type(odd)', 'props': [('background-color', '#f9f9f9')]}
])
display(styled_df)


# In[45]:


algeria_cell_sites_gdf["radio"].value_counts()


# In[46]:


# Create blank dataframe with id, latitute and longitude columns
formatted_algeria_cell_sites = extract_lat_lon(algeria_cell_sites_gdf, id_column='ict_id')
formatted_algeria_cell_sites["radio_type"] = algeria_cell_sites_gdf["radio"]
formatted_algeria_cell_sites["antenna_height_m"] = 25
formatted_algeria_cell_sites["backhaul_type"] = pd.NA
formatted_algeria_cell_sites["backhaul_throughput_mbps"] = pd.NA
formatted_algeria_cell_sites["operator_name"] = pd.NA


# In[47]:


formatted_algeria_cell_sites.head()
# data_table.DataTable(formatted_algeria_schools, num_rows_per_page=10)


# In[68]:


formatted_algeria_cell_sites.to_csv(os.path.join(data_directory, "formatted_algeria_cell_sites.csv"), index=False)


# ## Transmission node data

# In[48]:


node_metadata = pd.DataFrame({
   'column_name': ['ict_id', 'dataset_id', 'latitude', 'longitude', 'operator_name', 'infrastructure_type', 'node_status', 'equipped_capacity_mbps', 'potential_capacity_mbps'],
   'column_type': ['UUID', 'UUID', 'float', 'float', 'string', 'string', 'string', 'float', 'float'],
   'levels': [
       '',  # node_id
       '',  # dataset_id
       '',  # latitude
       '',  # longitude
       '',  # operator_name
       'fiber, microwave, other',  # infrastructure_type
       'operational, planned, under construction',  # node_status
       '',  # equipped_capacity_mbps
       ''   # potential_capacity_mbps
   ],
   'example': ['123e4567-e89b-12d3-a456-426614174000', '987fcdeb-51a2-12d3-a456-426614174000', '38.988755', '1.401938', 'TelOperator', 'fiber', 'operational', '1000', '2000'],
   'mandatory': ['Yes', 'Yes', 'Yes', 'Yes', 'No', 'Yes', 'Yes', 'No', 'No'],
   'definition': [
       'Node identifier',
       'Unique identifier for the dataset',
       'Geographical latitude',
       'Geographical longitude',
       'Name of the mobile operator',
       'Type of Infrastructure',
       'Status of the node',
       'Equipped bandwidth ready for use to connect subscribers',
       'Total theoretical bandwidth available for subscriber connections'
   ]
})

styled_df = node_metadata.style.set_properties(**{
   'text-align': 'left',
   'border': '1px solid black',
   'padding': '8px'
}).set_table_styles([
   {'selector': 'thead', 'props': [('background-color', '#f2f2f2'), ('font-weight', 'bold'), ('border-bottom', '2px solid black')]},
   {'selector': 'tbody tr:nth-of-type(odd)', 'props': [('background-color', '#f9f9f9')]}
])
display(styled_df)


# In[49]:


algeria_nodes_gdf["type_infr"].value_counts()   


# In[50]:


# Create blank dataframe with id, latitute and longitude columns
formatted_algeria_nodes = extract_lat_lon(algeria_nodes_gdf, id_column='ict_id')
formatted_algeria_nodes
formatted_algeria_nodes["operator_name"] = pd.NA
formatted_algeria_nodes["infrastructure_type"] = "fiber"
formatted_algeria_nodes["node_status"] = "operational"
formatted_algeria_nodes["equipped_capacity_mbps"] = pd.NA
formatted_algeria_nodes["potential_capacity_mbps"] = pd.NA


# In[51]:


formatted_algeria_nodes.head()
# data_table.DataTable(formatted_algeria_schools, num_rows_per_page=10)


# In[69]:


formatted_algeria_nodes.to_csv(os.path.join(data_directory, "formatted_algeria_nodes.csv"), index=False)


# ## Mobile coverage

# In[52]:


coverage_metadata = pd.DataFrame({
   'column_name': ['coverage_id', 'dataset_id', 'signal_strength_dbm', 'operator_name', 'geometry', 'coverage'],
   'column_type': ['UUID', 'UUID', 'float', 'string', 'geometry', 'integer'],
   'levels': [
       '',  # coverage_id
       '',  # dataset_id
       '',  # signal_strength
       '',  # operator_name
       'polygon',  # geometry
       '1'
   ],
   'example': [
       '123e4567-e89b-12d3-a456-426614174000', 
       '987fcdeb-51a2-12d3-a456-426614174000', 
       '-93', 
       'TelOperator',
       'POLYGON((...))',
       '1'
   ],
   'mandatory': ['Yes', 'Yes', 'Yes', 'No', 'Yes', 'Yes'],
   'definition': [
       'Unique identifier for the coverage area',
       'Unique identifier for the dataset',
       'Mobile signal strength in dBm for coverage',
       'Name of the mobile operator',
       'Polygon geometry of coverage area',
       'Binary value indicating coverage'
   ]
})

styled_df = coverage_metadata.style.set_properties(**{
   'text-align': 'left',
   'border': '1px solid black',
   'padding': '8px'
}).set_table_styles([
   {'selector': 'thead', 'props': [('background-color', '#f2f2f2'), ('font-weight', 'bold'), ('border-bottom', '2px solid black')]},
   {'selector': 'tbody tr:nth-of-type(odd)', 'props': [('background-color', '#f9f9f9')]}
])
display(styled_df)


# In[53]:


algeria_clipped_mobile_coverage_gdf


# In[54]:


# Create blank dataframe with id, latitute and longitude columns
formatted_algeria_coverage = algeria_clipped_mobile_coverage_gdf
formatted_algeria_coverage["coverage"] = 1
formatted_algeria_coverage["signal_strength_dbm"] = -93
formatted_algeria_coverage["operator_name"] = pd.NA
formatted_algeria_coverage["coverage_id"] = [str(uuid.uuid4()) for _ in range(len(formatted_algeria_coverage))]
formatted_algeria_coverage["dataset_id"] = str(uuid.uuid4())


# In[55]:


formatted_algeria_coverage.head()
# data_table.DataTable(formatted_algeria_schools, num_rows_per_page=10)


# In[70]:


formatted_algeria_coverage.to_file(os.path.join(data_directory, "formatted_algeria_coverage.geojson"), driver="GeoJSON")

