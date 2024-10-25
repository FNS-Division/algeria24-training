# def find_close_points(gdf, distance=200):
#     """
#     Find points in a GeoDataFrame that are within a certain distance of each other.

#     Parameters:
#     gdf (GeoDataFrame): GeoDataFrame containing point geometries.
#     distance (float): Distance threshold in meters (default is 50 meters).
#     """
#     gdf = gdf.copy().to_crs(gdf.estimate_utm_crs())
#     gdf["buffer"] = gdf["geometry"].buffer(distance)
#     close_points = gpd.sjoin(gdf, gdf.set_geometry('buffer'), predicate='intersects', how='inner')
#     close_points = close_points[close_points.index != close_points['index_right']]
#     close_points['sorted_index'] = close_points.apply(lambda row: tuple(sorted([row.name, row['index_right']])), axis=1)
#     close_points = close_points.sort_values('sorted_index').reset_index()
#     close_points = close_points.set_geometry('geometry_left').to_crs("EPSG:4326")
#     return close_points