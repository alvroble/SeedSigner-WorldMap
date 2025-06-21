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

def get_country_name_variants(name):
    try:
        country = pycountry.countries.lookup(name)
        return {country.name, getattr(country, 'official_name', '')}
    except LookupError:
        return {name}

# Load world map data
gdf = gpd.read_file("data/ne_110m_admin_0_countries.shp")
gdf = gdf.to_crs("+proj=wintri")

highlighted_variants = set()
for name in highlighted:
    highlighted_variants |= {v for v in get_country_name_variants(name) if v}
highlighted_variants = {v.lower().strip() for v in highlighted_variants}

unsupported = []
admin_values = set(gdf['ADMIN'].str.lower().str.strip().values)
sovereignt_values = set(gdf['SOVEREIGNT'].str.lower().str.strip().values)
all_values = admin_values | sovereignt_values
for name in highlighted:
    variants = {v.lower().strip() for v in get_country_name_variants(name) if v}
    found = any(v in all_values for v in variants)
    if not found:
        unsupported.append(name)

if unsupported:
    print('The following countries are not supported and will not be highlighted:')
    for c in unsupported:
        print('  -', c)

# Add a column to indicate if a country is partially supported
partial_support_variants = set()
for name in partial_support:
    partial_support_variants |= {v.lower().strip() for v in get_country_name_variants(name) if v}

def is_highlighted(row):
    admin = row['ADMIN'].lower().strip()
    sovereignt = row['SOVEREIGNT'].lower().strip()
    return (
        admin in highlighted_variants
        or sovereignt in highlighted_variants
        or admin in MANUALLY_HIGHLIGHTED
        or sovereignt in MANUALLY_HIGHLIGHTED
    )

def is_partially_supported(row):
    return (row['ADMIN'].lower().strip() in partial_support_variants) or (row['SOVEREIGNT'].lower().strip() in partial_support_variants)

gdf['highlight'] = gdf.apply(is_highlighted, axis=1)
gdf['partially_supported'] = gdf.apply(is_partially_supported, axis=1)

dark_bg = '#1a1a1a'
cool_country = '#323232'
orange = '#ff9f0a'

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
plt.savefig('world_map.png', dpi=400, facecolor=dark_bg, bbox_inches='tight', pad_inches=0.1)
plt.savefig('world_map.svg', format='svg', facecolor=dark_bg, bbox_inches='tight', pad_inches=0.1)
print('Map saved as world_map.png and world_map.svg')