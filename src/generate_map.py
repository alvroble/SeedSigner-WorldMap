"""
SeedSigner-WorldMap
A tool for generating a dark-themed world map with highlighted and patterned countries, logo overlay, and high-quality output.

This map highlights all countries whose official languages are currently supported by the latest SeedSigner release.
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import pycountry
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
import os

# List of countries to always highlight (lowercase)
# Manually highlighted because for some reason they don't get colored from the file
MANUALLY_HIGHLIGHTED = ['venezuela', 'bolivia']

# Read highlighted countries from file
# Update highlighted_countries.txt to include all countries whose official languages are supported by SeedSigner.
with open('highlighted_countries.txt', 'r') as f:
    highlighted = set(line.strip() for line in f if line.strip())

# Read partially supported countries from file
try:
    with open('partially_supported_countries.txt', 'r') as f:
        partial_support = set(line.strip().lower() for line in f if line.strip())
except FileNotFoundError:
    partial_support = set()

RELEASE_CODE = "v0.8.6"  # <-- Set your release code here

def read_country_list(filename, lowercase=False):
    try:
        with open(filename, 'r') as f:
            lines = set(line.strip() for line in f if line.strip())
            if lowercase:
                return set(l.lower() for l in lines)
            return lines
    except FileNotFoundError:
        return set()

def get_country_name_variants(name):
    try:
        country = pycountry.countries.lookup(name)
        return {country.name, getattr(country, 'official_name', '')}
    except LookupError:
        return {name}

def prepare_highlighted_variants(highlighted):
    highlighted_variants = set()
    for name in highlighted:
        highlighted_variants |= {v for v in get_country_name_variants(name) if v}
    return {v.lower().strip() for v in highlighted_variants}

def prepare_partial_support_variants(partial_support):
    partial_support_variants = set()
    for name in partial_support:
        partial_support_variants |= {v.lower().strip() for v in get_country_name_variants(name) if v}
    return partial_support_variants

def is_highlighted(row, highlighted_variants, manually_highlighted):
    admin = row['ADMIN'].lower().strip()
    sovereignt = row['SOVEREIGNT'].lower().strip()
    return (
        admin in highlighted_variants
        or sovereignt in highlighted_variants
        or admin in manually_highlighted
        or sovereignt in manually_highlighted
    )

def is_partially_supported(row, partial_support_variants):
    return (
        row['ADMIN'].lower().strip() in partial_support_variants
        or row['SOVEREIGNT'].lower().strip() in partial_support_variants
    )

def plot_map(gdf, highlighted_variants, partial_support_variants, manually_highlighted, orange, dark_bg, cool_country):
    gdf['highlight'] = gdf.apply(lambda row: is_highlighted(row, highlighted_variants, manually_highlighted), axis=1)
    gdf['partially_supported'] = gdf.apply(lambda row: is_partially_supported(row, partial_support_variants), axis=1)

    fig, ax = plt.subplots(figsize=(16, 9), facecolor=dark_bg)
    plt.style.use('dark_background')
    ax.set_facecolor(dark_bg)

    # Plot background countries
    background = gdf[(gdf['highlight'] == False) & (gdf['partially_supported'] == False)]
    background.plot(ax=ax, color=cool_country, edgecolor='#222831', linewidth=0.5)

    # Plot solid highlighted countries (not partially supported)
    solid = gdf[(gdf['highlight'] == True) & (gdf['partially_supported'] == False)]
    solid.plot(ax=ax, color=orange, edgecolor='white', linewidth=1.2)

    # Plot partially supported countries (solid orange with diagonal hatch)
    partial_gdf = gdf[gdf['partially_supported'] == True]
    if not partial_gdf.empty:
        partial_gdf.plot(ax=ax, facecolor=orange, edgecolor='white', linewidth=1.5, hatch='///', zorder=3)

    # Add logo and release code
    try:
        logo_img = mpimg.imread('logo.png')
        imagebox = OffsetImage(logo_img, zoom=0.03)
        ab = AnnotationBbox(imagebox, (0.5, 1.08), frameon=False, xycoords='axes fraction', box_alignment=(0.5, 1.0))
        ax.add_artist(ab)
        # Add release code below the logo (smaller and lower)
        ax.text(0.5, 0.99, RELEASE_CODE, color=orange, fontsize=12, fontweight='bold', ha='center', va='top', transform=ax.transAxes)
    except FileNotFoundError:
        # Add release code even if logo is missing (smaller and lower)
        ax.text(0.5, 0.99, RELEASE_CODE, color=orange, fontsize=12, fontweight='bold', ha='center', va='top', transform=ax.transAxes)

    ax.axis('off')
    plt.tight_layout()
    plt.savefig('output/world_map.png', dpi=400, facecolor=dark_bg, bbox_inches='tight', pad_inches=0.1)
    plt.savefig('output/world_map.svg', format='svg', facecolor=dark_bg, bbox_inches='tight', pad_inches=0.1)
    print('Map saved as output/world_map.png and output/world_map.svg')

def main():
    MANUALLY_HIGHLIGHTED = ['venezuela', 'bolivia']
    highlighted = read_country_list('highlighted_countries.txt')
    partial_support = read_country_list('partially_supported_countries.txt', lowercase=True)

    gdf = gpd.read_file("data/ne_110m_admin_0_countries.shp")
    gdf = gdf.to_crs("+proj=wintri")

    highlighted_variants = prepare_highlighted_variants(highlighted)
    partial_support_variants = prepare_partial_support_variants(partial_support)

    # Warn about unsupported countries
    admin_values = set(gdf['ADMIN'].str.lower().str.strip().values)
    sovereignt_values = set(gdf['SOVEREIGNT'].str.lower().str.strip().values)
    all_values = admin_values | sovereignt_values
    unsupported = []
    for name in highlighted:
        variants = {v.lower().strip() for v in get_country_name_variants(name) if v}
        found = any(v in all_values for v in variants)
        if not found:
            unsupported.append(name)
    if unsupported:
        print('The following countries are not supported and will not be highlighted:')
        for c in unsupported:
            print('  -', c)

    dark_bg = '#1a1a1a'
    cool_country = '#323232'
    orange = '#ff9f0a'

    plot_map(gdf, highlighted_variants, partial_support_variants, MANUALLY_HIGHLIGHTED, orange, dark_bg, cool_country)

if __name__ == "__main__":
    main()