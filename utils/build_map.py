import json

try:
    import geopandas as gpd
except Exception:
    gpd = None


def build_map(shp_path: str, output_json: str = "map_paths.json"):
    if gpd is None:
        raise RuntimeError("geopandas is required for this utility")

    gdf = gpd.read_file(shp_path)
    gdf = gdf.to_crs("EPSG:4326")
    gdf["geometry"] = gdf.boundary
    gdf["geometry"] = gdf.simplify(tolerance=0.001, preserve_topology=True)
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()

    def line_to_svg_path(geom):
        if geom is None or geom.is_empty:
            return ""
        if geom.geom_type == "LineString":
            coords = list(geom.coords)
            return "M " + " L ".join(f"{x},{y}" for x, y in coords) if coords else ""
        if geom.geom_type == "MultiLineString":
            paths = []
            for line in geom.geoms:
                coords = list(line.coords)
                if coords:
                    paths.append("M " + " L ".join(f"{x},{y}" for x, y in coords))
            return " ".join(paths)
        return ""

    gdf["svg"] = gdf.geometry.apply(line_to_svg_path)
    gdf = gdf[gdf["svg"] != ""].copy()
    svg_data = [
        {"id": str(row.get("SIGUNGU_CD", "")), "name": row.get("SIGUNGU_NM", ""), "path": row["svg"]}
        for _, row in gdf.iterrows()
    ]
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(svg_data, f, ensure_ascii=False, indent=2)
    return output_json
