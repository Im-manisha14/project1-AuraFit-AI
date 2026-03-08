"""
migrate_v2.py
=============
Full structured outfit dataset.
- Adds 3 new attribute columns: category, pattern, sleeve_type
- Deletes all old outfits (and related rows) and inserts 100 proper structured ones
- Every outfit has unique, outfit-specific image keywords for source.unsplash.com

Run:  python migrate_v2.py
"""
import sqlite3, json, os

DB = os.path.join(os.path.dirname(__file__), 'aurafit.db')

def img(keywords, sig):
    """Return a source.unsplash.com URL with outfit-specific keywords and a unique sig."""
    return f"https://source.unsplash.com/600x900/?{keywords}&sig={sig}"

# ---------------------------------------------------------------------------
# Outfit definitions — all 100 outfits
# ---------------------------------------------------------------------------
OUTFITS = []      # filled by add()  (sig auto-increments)
_S = [1]          # mutable counter so nested calls share state

def add(name, desc, gender, occ, season, cat, style, colors, pattern, sleeve,
        top, bottom, shoes, acc, fabrics, compat, comfort, trending, tscore, kw):
    _S[0] += 1
    OUTFITS.append({
        'name': name, 'description': desc, 'gender': gender,
        'occasion': occ, 'season': season, 'category': cat,
        'style_type': style, 'colors': colors, 'pattern': pattern,
        'sleeve_type': sleeve, 'top': top, 'bottom': bottom, 'shoes': shoes,
        'accessories': acc, 'fabric_types': fabrics,
        'body_type_compatibility': compat, 'comfort_score': comfort,
        'is_trending': trending, 'trend_score': tscore,
        'image_url': img(kw, _S[0] * 97),   # * prime keeps sigs well-spread
    })

# ═══════════════════════════════════════════════════════════════════════════
# MALE FORMAL
# ═══════════════════════════════════════════════════════════════════════════
add("Classic Black Tuxedo",
    "Timeless black tuxedo with satin lapels — the gold standard for black-tie events.",
    'male','formal','all','tuxedo','black-tie',
    ['black','white'],'solid','full',
    'Tuxedo Jacket & Dress Shirt','Tuxedo Trousers','Patent Leather Oxfords',
    ['Bow Tie','Cufflinks','Pocket Square'],['wool','cotton'],
    ['athletic','average','muscular','slim'],0.68,False,0.72,
    'men+black+tuxedo+formal+bow+tie+elegant')

add("Navy Pinstripe Suit",
    "Sharp navy pinstripe suit for commanding professional presence.",
    'male','formal','all','suit','formal',
    ['navy','white'],'pinstripe','full',
    'Navy Blazer & White Dress Shirt','Pinstripe Trousers','Oxford Shoes',
    ['Silk Tie','Leather Belt'],['wool','cotton'],
    ['athletic','average','muscular','slim','heavy'],0.72,True,0.85,
    'men+navy+pinstripe+suit+formal+tie')

add("Charcoal Grey Formal Suit",
    "Clean charcoal suit with slim lapels — sophisticated at any formal event.",
    'male','formal','all','suit','formal',
    ['charcoal','light blue'],'solid','full',
    'Slim Blazer & Light Blue Shirt','Slim Trousers','Derby Shoes',
    ['Silver Tie'],['wool','cotton'],
    ['slim','average','athletic'],0.75,True,0.82,
    'men+charcoal+grey+slim+suit+formal')

add("Royal Blue Wedding Suit",
    "Bold royal blue suit — made for weddings and celebrations.",
    'male','formal','spring','suit','formal',
    ['royal blue','white'],'solid','full',
    'Bold Blue Blazer & White Shirt','Tailored Trousers','White Leather Shoes',
    ['Pocket Square'],['wool','cotton'],
    ['athletic','average','slim'],0.74,True,0.88,
    'men+royal+blue+wedding+suit+celebration')

add("White Linen Formal Suit",
    "Crisp white linen suit — effortlessly refined for summer formals.",
    'male','formal','summer','suit','formal',
    ['white','cream'],'solid','full',
    'White Linen Blazer & Dress Shirt','White Linen Trousers','Tan Loafers',
    ['Brown Belt'],['linen'],
    ['slim','average','athletic'],0.78,True,0.80,
    'men+white+linen+summer+suit+formal')

add("Black Double-Breasted Suit",
    "Double-breasted black suit — authority delivered with dramatic flair.",
    'male','formal','all','suit','formal',
    ['black','silver'],'solid','full',
    'Double-Breasted Blazer & Dress Shirt','Tailored Trousers','Patent Black Oxfords',
    ['Silver Tie','Pocket Square'],['wool'],
    ['muscular','heavy','average'],0.70,False,0.74,
    'men+black+double+breasted+suit+formal')

add("Burgundy Velvet Evening Suit",
    "Rich burgundy velvet suit for glamorous formal evenings.",
    'male','formal','fall','suit','formal',
    ['burgundy','black'],'solid','full',
    'Velvet Blazer & Black Turtleneck','Velvet Trousers','Black Oxford Shoes',
    ['Lapel Pin'],['velvet','cotton'],
    ['slim','athletic','average'],0.71,True,0.91,
    'men+burgundy+velvet+suit+evening+formal')

add("Camel Herringbone Suit",
    "Refined camel herringbone tweed for sophisticated autumn formals.",
    'male','formal','fall','suit','formal',
    ['camel','warm brown','cream'],'herringbone','full',
    'Herringbone Blazer & White Shirt','Herringbone Trousers','Brown Derby Shoes',
    ['Knit Tie'],['tweed','wool'],
    ['average','heavy','muscular'],0.73,False,0.77,
    'men+camel+herringbone+tweed+suit+autumn')

add("Forest Green Statement Suit",
    "Forest green statement suit for formal evenings that demand attention.",
    'male','formal','all','suit','formal',
    ['forest green','black'],'solid','full',
    'Forest Green Blazer & Black Turtleneck','Tailored Trousers','Black Oxford Shoes',
    ['Minimalist Watch'],['wool','cotton'],
    ['slim','average'],0.72,True,0.89,
    'men+green+suit+evening+statement+formal')

add("Classic Morning Coat",
    "Traditional morning coat — the most distinguished daytime formal attire.",
    'male','formal','all','morning coat','black-tie',
    ['charcoal','grey','black'],'striped','full',
    'Morning Coat & Dress Shirt & Waistcoat','Striped Formal Trousers','Black Patent Shoes',
    ['Cravat'],['wool','cotton'],
    ['slim','average'],0.60,False,0.65,
    'men+morning+coat+traditional+ceremony+formal')

# ═══════════════════════════════════════════════════════════════════════════
# FEMALE FORMAL
# ═══════════════════════════════════════════════════════════════════════════
add("Classic Black Evening Gown",
    "Floor-length black silk gown with a subtle slit — timeless sophistication.",
    'female','formal','all','gown','elegant',
    ['black'],'solid','sleeveless',
    'Strapless Black Gown (full)','N/A','Stiletto Heels',
    ['Diamond Earrings','Evening Clutch'],['silk','satin'],
    ['hourglass','pear','rectangle'],0.62,True,0.90,
    'women+black+evening+gown+formal+elegant+silk')

add("Navy Formal Pantsuit",
    "Structured navy woman's pantsuit — powerful and polished boardroom look.",
    'female','formal','all','pantsuit','power-dressing',
    ['navy','white'],'solid','full',
    'Blazer & Silk Blouse','Wide-Leg Trousers','Block Heels',
    ['Statement Earrings'],['polyester','silk'],
    ['apple','inverted_triangle','rectangle'],0.72,True,0.84,
    'women+navy+pantsuit+formal+professional+power')

add("Emerald Floor-Length Gown",
    "Stunning off-shoulder emerald gown that commands attention.",
    'female','formal','all','gown','glam',
    ['emerald','gold'],'solid','sleeveless',
    'Off-Shoulder Emerald Gown (full)','N/A','Gold Heels',
    ['Gold Cuff','Clutch'],['chiffon','satin'],
    ['hourglass','pear','rectangle'],0.65,True,0.93,
    'women+emerald+green+floor+length+gown+formal')

add("Red Formal Sheath Dress",
    "Scarlet sheath dress — confident, sophisticated, and unforgettable.",
    'female','formal','all','sheath dress','elegant',
    ['red','black'],'solid','sleeveless',
    'Fitted Red Sheath Dress (full)','N/A','Black Pointed Heels',
    ['Pearl Earrings'],['polyester','crepe'],
    ['hourglass','rectangle'],0.68,True,0.87,
    'women+red+sheath+dress+formal+elegant')

add("Blush Pink Ball Gown",
    "Romantic strapless ball gown in soft blush — made for galas.",
    'female','formal','spring','gown','feminine',
    ['blush','pink','rose'],'solid','sleeveless',
    'Strapless Ball Gown (full)','N/A','Nude Heels',
    ['Rose Gold Jewelry'],['tulle','satin'],
    ['pear','rectangle','hourglass'],0.60,True,0.85,
    'women+pink+blush+ball+gown+formal+princess')

add("Ivory Column Dress",
    "Minimalist ivory column dress — the very definition of understated elegance.",
    'female','formal','all','column dress','minimalist',
    ['ivory','cream'],'solid','sleeveless',
    'Ivory Column Dress (full)','N/A','Nude Pumps',
    ['Minimalist Gold Jewel'],['silk'],
    ['rectangle','inverted_triangle'],0.70,True,0.83,
    'women+ivory+column+minimalist+dress+formal')

add("Midnight Blue Mermaid Gown",
    "Sultry mermaid gown in midnight blue — made for formal galas.",
    'female','formal','all','gown','glam',
    ['navy','midnight blue'],'solid','sleeveless',
    'Midnight Mermaid Gown (full)','N/A','Strappy Silver Heels',
    ['Diamond Necklace'],['sequin','chiffon'],
    ['hourglass','pear'],0.63,True,0.89,
    'women+midnight+blue+mermaid+gown+formal+sequin')

add("Wine Red Pleated Formal Dress",
    "Flowing wine-red pleated long-sleeve dress — elegant and refined.",
    'female','formal','fall','dress','elegant',
    ['burgundy','wine'],'pleated','full',
    'Long-Sleeve Pleated Dress (full)','N/A','Nude Pumps',
    ['Gold Earrings'],['chiffon'],
    ['all'],0.72,False,0.78,
    'women+wine+burgundy+pleated+dress+formal+long+sleeve')

add("White Formal Trouser Suit",
    "Crisp white tailored trouser suit — modern power dressing at its finest.",
    'female','formal','summer','trouser suit','power-dressing',
    ['white','cream'],'solid','full',
    'Structured White Blazer & Blouse','Wide-Leg White Trousers','White Pumps',
    ['Gold Watch'],['linen','cotton'],
    ['inverted_triangle','rectangle','apple'],0.73,True,0.82,
    'women+white+trouser+suit+formal+power+dressing')

add("Classic Black Blazer Formal Set",
    "Sleek black blazer with tailored trousers — executive elegance.",
    'female','formal','all','blazer set','formal',
    ['black','white'],'solid','full',
    'Fitted Black Blazer & White Shirt','Black Trousers','Black Pumps',
    ['Pearl Necklace'],['polyester','cotton'],
    ['all'],0.74,True,0.86,
    'women+black+blazer+formal+professional+executive')

# ═══════════════════════════════════════════════════════════════════════════
# MALE CASUAL
# ═══════════════════════════════════════════════════════════════════════════
add("White Tee & Classic Blue Jeans",
    "The essential white tee with straight blue jeans — effortless everyday style.",
    'male','casual','all','t-shirt','casual',
    ['white','blue'],'solid','half',
    'White Crew-Neck T-Shirt','Straight Blue Jeans','White Sneakers',
    ['Minimal Watch'],['cotton','denim'],
    ['all'],0.95,False,0.70,
    'men+white+tshirt+blue+jeans+street+casual')

add("Olive Cargo Pants Outfit",
    "Olive cargo pants with a neutral tee — urban utility and style.",
    'male','casual','fall','cargo pants','streetwear',
    ['olive','khaki','white'],'solid','half',
    'Cream Plain Tee','Olive Cargo Pants','Beige Desert Boots',
    ['Canvas Tote'],['cotton'],
    ['slim','average','athletic'],0.90,True,0.85,
    'men+olive+cargo+pants+streetwear+casual')

add("Denim Jacket & Cream Chinos",
    "Classic denim jacket over a white tee with relaxed chinos.",
    'male','casual','spring','denim jacket','casual',
    ['blue','beige','white'],'solid','full',
    'Denim Jacket & White Tee','Beige Chinos','White Leather Sneakers',
    ['Sunglasses'],['denim','cotton'],
    ['slim','average','athletic'],0.88,True,0.82,
    'men+denim+jacket+chinos+casual+spring')

add("Navy Striped Polo & Shorts",
    "Nautical striped polo with tailored shorts — effortless summer charm.",
    'male','casual','summer','polo','smart-casual',
    ['navy','white'],'stripes','half',
    'Striped Polo Shirt','Tailored Khaki Shorts','Espadrilles',
    ['Cap'],['cotton','polyester'],
    ['average','athletic'],0.92,False,0.72,
    'men+navy+striped+polo+shorts+summer')

add("Burgundy Hoodie & Slim Joggers",
    "Cozy burgundy hoodie with slim joggers — elevated casual wear.",
    'male','casual','winter','hoodie','casual',
    ['burgundy','grey'],'solid','full',
    'Zip-Up Burgundy Hoodie','Slim Grey Joggers','Running Sneakers',
    ['Beanie'],['cotton','fleece'],
    ['slim','average','heavy'],0.96,True,0.88,
    'men+burgundy+hoodie+joggers+street+casual')

add("Light Blue Linen Shirt & Khakis",
    "Relaxed linen shirt with khaki chinos — casual refinement for warm days.",
    'male','casual','summer','linen shirt','smart-casual',
    ['light blue','khaki','beige'],'solid','half',
    'Light Blue Linen Casual Shirt','Khaki Slim Chinos','Tan Loafers',
    ['Leather Bracelet'],['linen','cotton'],
    ['average','athletic','slim'],0.91,False,0.74,
    'men+linen+shirt+khaki+chinos+summer+casual')

add("Black Graphic Tee & Ripped Jeans",
    "Bold graphic tee with ripped jeans — authentic street style.",
    'male','casual','all','graphic tee','streetwear',
    ['black','blue'],'graphic','half',
    'Black Graphic Print Tee','Light-Wash Ripped Jeans','High-Top Sneakers',
    ['Chain Necklace','Snapback Cap'],['cotton','denim'],
    ['slim','athletic'],0.89,True,0.90,
    'men+graphic+tee+ripped+jeans+streetwear+hiphop')

add("Olive Bomber & Dark Slim Jeans",
    "Casual-cool olive bomber jacket layered over dark slim jeans.",
    'male','casual','fall','bomber jacket','casual',
    ['olive','black'],'solid','full',
    'Olive Bomber Jacket & Grey Tee','Dark Slim Jeans','Black Leather Boots',
    ['Sunglasses'],['nylon','denim'],
    ['slim','average','athletic'],0.87,True,0.84,
    'men+olive+bomber+jacket+dark+jeans+fall')

add("Grey Henley & Chino Shorts",
    "Casual henley button-up with chino shorts — warm-weather ease.",
    'male','casual','summer','henley','casual',
    ['grey','beige'],'solid','half',
    'Grey Henley Top','Beige Chino Shorts','Slip-On Sneakers',
    [],['cotton'],
    ['average','slim','athletic'],0.93,False,0.69,
    'men+grey+henley+shorts+casual+relaxed+summer')

add("Red Flannel Shirt & Dark Jeans",
    "Classic red-and-navy flannel paired with dark slim jeans — autumn staple.",
    'male','casual','fall','flannel shirt','casual',
    ['red','navy'],'check','full',
    'Open Flannel Shirt over White Tee','Dark Slim Jeans','Leather Boots',
    [],['flannel','denim'],
    ['average','heavy','muscular'],0.90,False,0.71,
    'men+flannel+plaid+shirt+jeans+fall+casual')

# ═══════════════════════════════════════════════════════════════════════════
# FEMALE CASUAL
# ═══════════════════════════════════════════════════════════════════════════
add("Floral Wrap Midi Dress",
    "Feminine floral wrap midi dress — effortless warm-weather chic.",
    'female','casual','spring','midi dress','feminine',
    ['pink','white','green'],'floral','half',
    'Floral Wrap Midi Dress (full)','N/A','White Strappy Mules',
    ['Dainty Necklace'],['chiffon','rayon'],
    ['hourglass','pear','rectangle'],0.86,True,0.88,
    'women+floral+wrap+midi+dress+spring+feminine')

add("White Crop Top & Mom Jeans",
    "Relaxed mom jeans with a clean white crop tee — effortless cool.",
    'female','casual','summer','crop top','casual',
    ['white','blue'],'solid','half',
    'White Cropped T-Shirt','High-Waist Mom Jeans','White Chunky Sneakers',
    ['Canvas Tote'],['cotton','denim'],
    ['apple','rectangle','inverted_triangle'],0.92,True,0.86,
    'women+white+crop+top+mom+jeans+casual+street')

add("Cream Oversized Sweater & Leggings",
    "Cozy oversized cream sweater with black fitted leggings — winter comfort.",
    'female','casual','winter','sweater','casual',
    ['cream','black'],'solid','full',
    'Oversized Cream Knit Sweater','Black High-Waist Leggings','Ankle Boots',
    ['Beanie'],['wool','cotton','spandex'],
    ['pear','hourglass','apple'],0.94,True,0.87,
    'women+oversized+sweater+cream+leggings+cozy+winter')

add("Denim Shorts & Striped Top",
    "Classic summer combo: striped top and denim shorts.",
    'female','casual','summer','shorts','casual',
    ['blue','white','navy'],'stripes','half',
    'Striped Fitted Tee','Light Wash Denim Shorts','White Sneakers',
    ['Tortoise Sunglasses'],['cotton','denim'],
    ['rectangle','inverted_triangle','apple'],0.93,False,0.74,
    'women+denim+shorts+striped+tshirt+casual+summer')

add("Pastel Yellow Sundress",
    "Airy pastel yellow sundress for sunny days — light and joyful.",
    'female','casual','summer','sundress','casual',
    ['yellow','cream'],'solid','sleeveless',
    'Sleeveless Sundress (full)','N/A','Strappy Tan Sandals',
    ['Straw Hat'],['cotton','linen'],
    ['all'],0.95,True,0.86,
    'women+yellow+sundress+summer+casual+sunny+light')

add("Black Blazer & Skinny Jeans",
    "Fitted blazer over a simple tee with slim jeans — smart casual perfection.",
    'female','casual','all','blazer','smart-casual',
    ['black','blue','white'],'solid','full',
    'Fitted Black Blazer & White Tee','Skinny Blue Jeans','Pointed-Toe Flats',
    [],['polyester','cotton','denim'],
    ['inverted_triangle','rectangle','apple'],0.85,True,0.85,
    'women+black+blazer+skinny+jeans+smart+casual')

add("Terracotta Boho Maxi Skirt & Tank",
    "Earthy boho maxi skirt with a neutral tank — carefree summer style.",
    'female','casual','summer','maxi skirt','bohemian',
    ['terracotta','cream','rust'],'print','sleeveless',
    'Neutral Fitted Tank Top','Flowy Boho Maxi Skirt','Woven Sandals',
    ['Layered Necklaces'],['rayon','cotton'],
    ['pear','rectangle','inverted_triangle'],0.88,True,0.83,
    'women+boho+maxi+skirt+terracotta+tank+summer')

add("Coral Sleeveless Romper",
    "Fun coral romper — playful and comfortable for casual days out.",
    'female','casual','summer','romper','casual',
    ['coral','peach'],'solid','sleeveless',
    'Sleeveless Romper (full)','N/A','Platform Sandals',
    ['Hoop Earrings'],['cotton','rayon'],
    ['all'],0.91,False,0.76,
    'women+coral+romper+casual+summer+playful')

add("Camel Turtleneck & Wide Cream Trousers",
    "Elevated camel ribbed turtleneck with wide-leg cream trousers.",
    'female','casual','fall','turtleneck','minimalist',
    ['camel','cream','beige'],'ribbed','full',
    'Ribbed Camel Turtleneck','Wide-Leg Cream Trousers','White Sneakers',
    ['Minimal Gold Earrings'],['wool','cotton'],
    ['apple','rectangle'],0.86,True,0.88,
    'women+camel+turtleneck+wide+leg+trousers+minimalist+fall')

add("Red Plaid Mini Skirt & Fitted Tee",
    "Y2K-inspired red plaid mini skirt with a fitted tee — retro chic.",
    'female','casual','fall','mini skirt','casual',
    ['red','black','white'],'plaid','half',
    'Fitted White Tee','Red Plaid Mini Skirt','Mary Jane Shoes',
    ['Mini Shoulder Bag'],['polyester','cotton'],
    ['rectangle','inverted_triangle'],0.84,True,0.82,
    'women+plaid+mini+skirt+fitted+tee+retro+casual')

# ═══════════════════════════════════════════════════════════════════════════
# MALE PARTY
# ═══════════════════════════════════════════════════════════════════════════
add("Burgundy Velvet Blazer",
    "Luxurious velvet blazer in deep burgundy — the life of any party.",
    'male','party','fall','blazer','glam',
    ['burgundy','black'],'solid','full',
    'Velvet Blazer & Black Dress Shirt','Black Slim Trousers','Black Chelsea Boots',
    ['Lapel Pin'],['velvet','cotton'],
    ['slim','average','athletic'],0.75,True,0.93,
    'men+velvet+burgundy+blazer+party+night+glam')

add("Silver Sequin Bomber Jacket",
    "Metallic silver sequin bomber — make the party remember you.",
    'male','party','all','bomber jacket','glam',
    ['silver','black'],'sequin','full',
    'Sequin Bomber Jacket & Black Tee','Black Slim Trousers','White Leather Sneakers',
    [],['sequin','polyester'],
    ['slim','athletic'],0.72,True,0.91,
    'men+silver+sequin+bomber+jacket+party+glam+night')

add("Floral Printed Silk Shirt & Trousers",
    "Lush floral silk shirt — bold, beautiful and perfect for celebrations.",
    'male','party','all','dress shirt','casual',
    ['multicolor','black'],'floral','full',
    'Floral Printed Silk Shirt','Black Slim Trousers','White Sneakers',
    [],['silk'],
    ['slim','average'],0.78,True,0.88,
    'men+printed+floral+silk+shirt+party+stylish')

add("Black Turtleneck & Dress Trousers",
    "Sleek black turtleneck with tailored trousers — minimalist party chic.",
    'male','party','fall','turtleneck','minimalist',
    ['black','charcoal'],'solid','full',
    'Fitted Black Turtleneck','Charcoal Dress Trousers','Black Chelsea Boots',
    ['Minimalist Watch'],['wool','polyester'],
    ['slim','athletic','average'],0.80,True,0.86,
    'men+black+turtleneck+party+minimalist+elegant+night')

add("Navy Satin-Lapel Blazer & Dark Jeans",
    "Elevated satin-lapel blazer with dark jeans — effortless party charisma.",
    'male','party','all','blazer','smart-casual',
    ['navy','black'],'solid','full',
    'Navy Satin-Lapel Blazer & Black Tee','Dark Slim Jeans','Black Loafers',
    [],['satin','cotton','denim'],
    ['average','athletic'],0.77,True,0.87,
    'men+navy+blazer+satin+lapel+party+smart+night')

add("Cobalt Blue Party Suit",
    "Vibrant cobalt blue suit — impossible to ignore at any celebration.",
    'male','party','all','suit','formal',
    ['royal blue','cobalt','white'],'solid','full',
    'Cobalt Blue Blazer & White Shirt','Cobalt Slim Trousers','White Leather Shoes',
    [],['wool','cotton'],
    ['slim','average','athletic'],0.74,True,0.90,
    'men+cobalt+blue+suit+party+bold+celebration')

add("Gold Embroidered Festive Kurta",
    "Rich gold-embroidered kurta with slim churidars — festive and distinguished.",
    'male','party','all','kurta','ethnic',
    ['gold','cream','maroon'],'embroidered','full',
    'Embroidered Kurta','Slim Churidar Pants','Mojri Juttis',
    ['Pocket Square'],['silk','cotton'],
    ['all'],0.78,True,0.84,
    'men+kurta+ethnic+gold+festive+indian+traditional')

add("White Linen Party Shirt & Trousers",
    "Crisp white linen — the Mediterranean party look refined to perfection.",
    'male','party','summer','dress shirt','resort',
    ['white','cream'],'solid','full',
    'White Linen Button-Down','White Linen Trousers','Tan Loafers',
    [],['linen'],
    ['average','slim','athletic'],0.82,False,0.78,
    'men+white+linen+shirt+trousers+party+summer+resort')

# ═══════════════════════════════════════════════════════════════════════════
# FEMALE PARTY
# ═══════════════════════════════════════════════════════════════════════════
add("Gold Sequin Mini Dress",
    "Show-stopping gold sequin mini dress for unforgettable party nights.",
    'female','party','all','mini dress','glam',
    ['gold','silver'],'sequin','sleeveless',
    'Gold Sequin Mini Dress (full)','N/A','Strappy Gold Heels',
    ['Evening Clutch'],['sequin','polyester'],
    ['hourglass','rectangle'],0.68,True,0.95,
    'women+gold+sequin+mini+dress+party+glam+night')

add("Black Bodycon Party Dress",
    "Sleek black bodycon dress — curves in all the right places.",
    'female','party','all','bodycon dress','elegant',
    ['black'],'solid','sleeveless',
    'Black Bodycon Dress (full)','N/A','Black Stilettos',
    ['Statement Earrings'],['spandex','polyester'],
    ['hourglass','pear'],0.65,True,0.90,
    'women+black+bodycon+dress+party+night+elegant')

add("Red Off-Shoulder Party Dress",
    "Bold red off-shoulder dress — effortlessly head-turning at any event.",
    'female','party','all','off-shoulder dress','glam',
    ['bright red','red'],'solid','sleeveless',
    'Off-Shoulder Red Dress (full)','N/A','Black Heels',
    ['Gold Earrings'],['polyester','rayon'],
    ['inverted_triangle','hourglass'],0.70,True,0.91,
    'women+red+off+shoulder+dress+party+night+bold')

add("Silver Metallic Mini Dress",
    "Futuristic silver metallic dress — the party looks at you first.",
    'female','party','all','mini dress','glam',
    ['silver','metallic'],'metallic','sleeveless',
    'Metallic Mini Dress (full)','N/A','Silver Heels',
    ['Silver Clutch'],['metallic fabric'],
    ['hourglass','rectangle'],0.64,True,0.89,
    'women+silver+metallic+mini+dress+party+club+glam')

add("Pink Floral Wrap Party Dress",
    "Playful floral wrap dress adding charm to every evening gathering.",
    'female','party','spring','wrap dress','feminine',
    ['pink','purple'],'floral','half',
    'Floral Wrap Dress (full)','N/A','Nude Heels',
    ['Dainty Earrings'],['chiffon'],
    ['hourglass','pear','rectangle'],0.78,True,0.85,
    'women+floral+pink+wrap+dress+party+spring+feminine')

add("Emerald Velvet Slip Dress",
    "Deep emerald velvet slip dress — mysterious, sensuous, unforgettable.",
    'female','party','fall','slip dress','elegant',
    ['emerald','dark green'],'solid','sleeveless',
    'Velvet Slip Dress (full)','N/A','Block Heel Mules',
    ['Thin Gold Necklace'],['velvet'],
    ['hourglass','rectangle'],0.70,True,0.87,
    'women+emerald+green+velvet+slip+dress+party+night')

add("Fuchsia Cocktail Dress",
    "Vivid fuchsia cocktail dress radiating confidence and energy.",
    'female','party','all','cocktail dress','glam',
    ['hot pink','fuchsia'],'solid','sleeveless',
    'Fuchsia Cocktail Dress (full)','N/A','Nude Pumps',
    ['Silver Clutch'],['crepe','polyester'],
    ['hourglass','pear','apple'],0.72,True,0.86,
    'women+fuchsia+pink+cocktail+dress+party+bold')

add("Embroidered Lehenga Choli",
    "Vibrant embroidered lehenga choli — festive splendour and tradition.",
    'female','party','all','lehenga','ethnic',
    ['maroon','gold','red'],'embroidered','half',
    'Embroidered Choli Top','Flared Lehenga Skirt','Mojri Juttis',
    ['Jhumka Earrings','Maang Tikka'],['silk','zari'],
    ['all'],0.70,True,0.88,
    'women+lehenga+choli+ethnic+maroon+gold+festive+indian')

# ═══════════════════════════════════════════════════════════════════════════
# MALE WORK
# ═══════════════════════════════════════════════════════════════════════════
add("Navy Blazer & Khaki Chinos",
    "Classic navy blazer over a crisp shirt — the timeless smart office staple.",
    'male','work','all','blazer','smart-casual',
    ['navy','white','khaki'],'solid','full',
    'Navy Wool Blazer & White Shirt','Slim Khaki Chinos','Brown Leather Loafers',
    ['Leather Watch'],['wool','cotton'],
    ['average','athletic','slim'],0.82,True,0.84,
    'men+navy+blazer+chinos+office+smart+casual+work')

add("Charcoal Grey Office Suit",
    "Essential charcoal grey office suit — the ultimate executive look.",
    'male','work','all','suit','formal',
    ['charcoal','light blue'],'solid','full',
    'Slim Blazer & Light Blue Dress Shirt','Slim Trousers','Dark Oxford Shoes',
    ['Silk Tie'],['wool','cotton'],
    ['slim','average','athletic'],0.75,True,0.83,
    'men+charcoal+grey+office+suit+professional+business')

add("Premium Polo & Dark Dress Trousers",
    "Premium polo shirt with tailored dark trousers — smart Friday wear.",
    'male','work','all','polo','smart-casual',
    ['navy','dark grey'],'solid','half',
    'Premium Navy Polo Shirt','Dark Slim Trousers','Dark Brown Loafers',
    ['Leather Watch'],['cotton','polyester'],
    ['average','heavy','athletic'],0.86,False,0.76,
    'men+polo+shirt+office+business+casual+work')

add("Camel Linen Blazer & Smart Chinos",
    "Breathable camel linen blazer for warm-office smart casual.",
    'male','work','spring','linen blazer','smart-casual',
    ['camel','earth tones','white'],'solid','full',
    'Camel Linen Blazer & White Shirt','Smart Chino Trousers','White Loafers',
    [],['linen'],
    ['slim','average'],0.87,True,0.85,
    'men+camel+linen+blazer+smart+casual+office')

add("White Oxford Shirt & Black Trousers",
    "Precision-pressed white Oxford with black tailored trousers — crisp authority.",
    'male','work','all','dress shirt','formal',
    ['white','black'],'solid','full',
    'White Oxford Button-Down Shirt','Classic Black Dress Trousers','Black Oxfords',
    ['Black Leather Belt'],['cotton','wool'],
    ['all'],0.78,False,0.72,
    'men+white+oxford+shirt+black+trousers+office+formal')

add("Windowpane Check Blazer",
    "Bold windowpane-check blazer with smart grey trousers — fashion-forward office.",
    'male','work','all','blazer','smart-casual',
    ['teal','charcoal'],'check','full',
    'Windowpane Blazer & White Shirt','Grey Smart Trousers','Brown Derby Shoes',
    [],['wool','cotton'],
    ['slim','average'],0.77,True,0.81,
    'men+check+windowpane+blazer+office+stylish+work')

add("Navy Merino Crewneck & Trousers",
    "Refined merino crewneck over dress trousers — polished even in winter.",
    'male','work','winter','sweater','smart-casual',
    ['navy','grey'],'solid','full',
    'Navy Merino Crewneck Sweater','Grey Slim Dress Trousers','Brown Leather Loafers',
    ['Leather Watch'],['merino wool','wool'],
    ['average','slim','heavy'],0.85,False,0.74,
    'men+merino+navy+sweater+office+trousers+smart+work')

add("All-Black Business Suit",
    "Sharp all-black business suit — the go-to for high-stakes meetings.",
    'male','work','all','suit','formal',
    ['black','white'],'solid','full',
    'Black Blazer & White Dress Shirt','Black Trousers','Black Oxford Shoes',
    ['Silk Black Tie'],['wool','cotton'],
    ['athletic','average','muscular'],0.72,False,0.78,
    'men+black+business+suit+office+meeting+formal+work')

# ═══════════════════════════════════════════════════════════════════════════
# FEMALE WORK
# ═══════════════════════════════════════════════════════════════════════════
add("White Silk Blouse & Black Pencil Skirt",
    "Silk blouse tucked into a fitted black pencil skirt — boardroom ready.",
    'female','work','all','pencil skirt','formal',
    ['white','black'],'solid','full',
    'Silk White Blouse','Black Pencil Skirt','Black Block Heels',
    ['Pearl Earrings'],['silk','polyester'],
    ['hourglass','pear'],0.74,True,0.85,
    'women+white+blouse+pencil+skirt+work+office+professional')

add("Navy Career Blazer Dress",
    "Structured navy blazer dress — takes you from morning meetings to evening events.",
    'female','work','all','blazer dress','power-dressing',
    ['navy','white'],'solid','full',
    'Navy Blazer Dress (full)','N/A','Nude Pumps',
    ['Thin Belt'],['polyester','cotton'],
    ['apple','rectangle','inverted_triangle'],0.76,True,0.87,
    'women+navy+blazer+dress+career+work+professional')

add("Teal Structured Midi Dress",
    "Sophisticated teal midi dress — your go-to three-season work staple.",
    'female','work','all','midi dress','formal',
    ['teal','navy'],'solid','half',
    'Structured Teal Midi Dress (full)','N/A','Block Heel Pumps',
    ['Gold Necklace'],['crepe','polyester'],
    ['hourglass','rectangle','pear'],0.77,True,0.84,
    'women+teal+midi+dress+office+work+professional')

add("Olive Blazer & Wide-Leg Trousers",
    "Oversized blazer with high-waist wide-leg trousers — fashion-forward office.",
    'female','work','all','blazer set','power-dressing',
    ['olive','beige','cream'],'solid','full',
    'Oversized Olive Blazer & Fitted Tee','Wide-Leg Cream Trousers','Loafers',
    [],['linen','cotton'],
    ['pear','inverted_triangle','apple'],0.82,True,0.86,
    'women+olive+blazer+wide+leg+trousers+work+fashion')

add("Blush Silk Blouse & A-Line Skirt",
    "Flowy blush silk blouse with an ivory A-line midi skirt — refined femininity.",
    'female','work','spring','a-line skirt','feminine',
    ['blush','ivory'],'solid','full',
    'Blush Silk Blouse','Ivory A-Line Midi Skirt','Nude Kitten Heels',
    ['Pearl Necklace'],['silk','polyester'],
    ['hourglass','pear','rectangle'],0.79,True,0.82,
    'women+blush+silk+blouse+aline+skirt+work+feminine')

add("Charcoal Tailored Jumpsuit",
    "Clean structured jumpsuit — effortless all-day work style with zero effort.",
    'female','work','all','jumpsuit','minimalist',
    ['charcoal','black'],'solid','full',
    'Tailored Charcoal Jumpsuit (full)','N/A','Pointed-Toe Pumps',
    ['Gold Earrings'],['polyester','cotton'],
    ['inverted_triangle','rectangle'],0.78,True,0.84,
    'women+charcoal+black+jumpsuit+tailored+work+minimalist')

add("Cobalt Blue Shirt Dress",
    "Rich cobalt A-line shirt dress — practical elegance for every workday.",
    'female','work','all','shirt dress','smart-casual',
    ['royal blue','cobalt'],'solid','full',
    'Cobalt Button-Down Shirt Dress (full)','N/A','Block Heels',
    ['Thin Belt'],['cotton','polyester'],
    ['apple','rectangle','pear'],0.81,False,0.77,
    'women+cobalt+blue+shirt+dress+work+office')

add("Mustard Power Blazer Set",
    "Bold mustard blazer with black straight trousers — unapologetic power dressing.",
    'female','work','all','blazer set','power-dressing',
    ['mustard','black'],'solid','full',
    'Mustard Power Blazer & White Shirt','Black Straight Trousers','Black Pumps',
    [],['wool','cotton'],
    ['inverted_triangle','rectangle'],0.76,True,0.88,
    'women+mustard+yellow+power+blazer+trousers+work')

# ═══════════════════════════════════════════════════════════════════════════
# MALE GYM
# ═══════════════════════════════════════════════════════════════════════════
add("Performance Running Set",
    "Technical moisture-wicking run tee and shorts for peak athletic performance.",
    'male','gym','all','athletic shorts','sporty',
    ['black','white'],'solid','half',
    'Moisture-Wicking Run Tee','Athletic Running Shorts','Running Sneakers',
    ['Sports Watch'],['polyester','nylon'],
    ['all'],0.97,True,0.92,
    'men+running+athletic+shorts+gym+fitness+performance')

add("Full-Length Compression Training Set",
    "Compression tights with tank for high-intensity training.",
    'male','gym','all','compression tights','sporty',
    ['black','cobalt'],'solid','sleeveless',
    'Sleeveless Compression Top','Black Compression Leggings','Training Shoes',
    [],['spandex','polyester'],
    ['athletic','muscular','slim'],0.95,False,0.78,
    'men+compression+training+tights+tank+gym+athlete')

add("Zip-Up Hoodie & Tapered Joggers",
    "Matching zip-up hoodie and tapered joggers — warm-up wardrobe done right.",
    'male','gym','fall','hoodie','sporty',
    ['grey','black'],'solid','full',
    'Zip-Up Athletic Hoodie','Tapered Jogger Pants','Running Sneakers',
    [],['cotton','polyester'],
    ['all'],0.93,True,0.88,
    'men+hoodie+joggers+gym+warmup+athletic+training')

add("Muscle Tank & Athletic Shorts",
    "Classic muscle tank with loose shorts — optimal for weight training.",
    'male','gym','all','tank top','sporty',
    ['grey','black'],'solid','sleeveless',
    'Muscle Tank Top','Loose Athletic Shorts','Training Shoes',
    [],['cotton','polyester'],
    ['muscular','athletic'],0.96,False,0.74,
    'men+muscle+tank+top+gym+weightlifting+shorts')

add("Full-Length Navy Tracksuit",
    "Sleek full tracksuit — warm-ups and studio sessions sorted.",
    'male','gym','all','tracksuit','sporty',
    ['navy','white'],'solid','full',
    'Track Jacket','Track Pants','Running Sneakers',
    ['Sports Cap'],['polyester'],
    ['all'],0.91,True,0.82,
    'men+navy+tracksuit+gym+athletic+sport+training')

add("Dry-Fit Long Sleeve & Training Shorts",
    "Long-sleeve moisture-wicking top with flexible cross-training shorts.",
    'male','gym','all','athletic shorts','sporty',
    ['olive','black'],'solid','full',
    'Long-Sleeve Dry-Fit Top','Cross-Training Shorts','Cross-Trainers',
    [],['polyester','nylon'],
    ['average','slim','athletic'],0.94,False,0.76,
    'men+longsleeve+dry+fit+training+shorts+gym+crossfit')

add("Athleisure Jogger & Jacket Set",
    "Stylish athleisure set — gym to street without changing.",
    'male','gym','all','joggers','sporty',
    ['burgundy','black'],'solid','full',
    'Athletic Track Jacket','Tapered Joggers','Lifestyle Sneakers',
    ['Baseball Cap'],['polyester','cotton'],
    ['slim','average'],0.89,True,0.85,
    'men+athleisure+jogger+jacket+set+casual+gym+street')

# ═══════════════════════════════════════════════════════════════════════════
# FEMALE GYM
# ═══════════════════════════════════════════════════════════════════════════
add("High-Waist Leggings & Sports Bra",
    "Iconic high-waist compression leggings with a supportive sports bra.",
    'female','gym','all','leggings','sporty',
    ['black','purple'],'solid','sleeveless',
    'Supportive Sports Bra','High-Waist Compression Leggings','Running Sneakers',
    ['Sports Watch'],['spandex','polyester'],
    ['hourglass','pear','apple'],0.97,True,0.94,
    'women+leggings+sports+bra+gym+fitness+workout+yoga')

add("Sage Green Yoga Set",
    "Calming sage yoga set in ultra-soft fabric — align and elevate.",
    'female','gym','all','yoga set','sporty',
    ['sage green','cream'],'solid','sleeveless',
    'Fitted Yoga Crop Top','Flared Yoga Pants','Bare feet / Yoga Mat',
    [],['nylon','spandex'],
    ['all'],0.98,True,0.88,
    'women+yoga+sage+green+set+wellness+fitness+pose')

add("Running Shorts & Dry-Fit Tank",
    "Light running shorts with a dry-fit tank — built for the open road.",
    'female','gym','all','athletic shorts','sporty',
    ['coral','white'],'solid','sleeveless',
    'Dry-Fit Tank Top','High-Waist Running Shorts','Running Shoes',
    [],['polyester'],
    ['all'],0.96,False,0.80,
    'women+running+shorts+tank+top+gym+outdoor+fitness')

add("Pink Seamless Workout Set",
    "Sculpted seamless two-piece — smooth, sweat-ready and stylish.",
    'female','gym','all','workout set','sporty',
    ['blush','pink'],'solid','sleeveless',
    'Seamless Crop Top','Seamless Workout Shorts','Training Sneakers',
    [],['nylon','spandex'],
    ['hourglass','rectangle'],0.95,True,0.89,
    'women+seamless+workout+pink+set+gym+sporty')

add("Crop Top & Wide Athletic Flares",
    "Sporty crop top with wide-leg flares — gym to street in one outfit.",
    'female','gym','all','athletic flares','sporty',
    ['black','white'],'solid','sleeveless',
    'Athletic Crop Top','Wide-Leg Athletic Flares','White Lifestyle Sneakers',
    ['Sports Watch'],['polyester','cotton'],
    ['pear','hourglass'],0.89,True,0.84,
    'women+crop+top+wide+leg+flares+athletic+gym+fashion')

add("Training Hoodie & Fleece Leggings",
    "Cozy training hoodie with fleece-lined leggings for cold-gym sessions.",
    'female','gym','winter','workout set','sporty',
    ['dark grey','black'],'solid','full',
    'Athletic Training Hoodie','Fleece-Lined High-Waist Leggings','Running Sneakers',
    [],['fleece','spandex'],
    ['all'],0.93,False,0.77,
    'women+hoodie+fleece+leggings+winter+training+gym')

add("Dance Crop & Coloured Shorts",
    "Vibrant crop and shorts set for dance fitness and Zumba energy.",
    'female','gym','all','athletic shorts','sporty',
    ['hot pink','fuchsia'],'solid','sleeveless',
    'Colourful Sports Crop Top','Coloured Athletic Shorts','Dance Sneakers',
    [],['polyester','nylon'],
    ['all'],0.96,True,0.83,
    'women+dance+zumba+crop+sports+shorts+colorful+fitness')

# ═══════════════════════════════════════════════════════════════════════════
# MALE DATE
# ═══════════════════════════════════════════════════════════════════════════
add("Smart Blazer & Dark Jeans Date Look",
    "Charcoal blazer over a crew-neck with dark jeans — effortlessly attractive.",
    'male','date','all','blazer','smart-casual',
    ['charcoal','navy','black'],'solid','full',
    'Charcoal Blazer & White Crew-Neck','Dark Slim Jeans','Black Chelsea Boots',
    ['Minimalist Watch'],['wool','cotton','denim'],
    ['all'],0.85,True,0.89,
    'men+blazer+dark+jeans+smart+date+night+romantic')

add("Fitted Black Turtleneck Date Night",
    "Fitted black turtleneck with tailored trousers — dark and magnetic.",
    'male','date','fall','turtleneck','minimalist',
    ['black','charcoal'],'solid','full',
    'Fitted Black Turtleneck','Tailored Charcoal Trousers','Black Leather Shoes',
    [],['wool','polyester'],
    ['slim','athletic'],0.83,True,0.87,
    'men+black+turtleneck+date+night+elegant+romantic')

add("White Oxford Shirt & Navy Chinos",
    "Clean Oxford shirt with navy slim chinos — always leaves an impression.",
    'male','date','all','dress shirt','smart-casual',
    ['white','navy','khaki'],'solid','full',
    'Tailored White Oxford Shirt','Navy Slim Chinos','Tan Suede Loafers',
    ['Classic Watch'],['cotton'],
    ['all'],0.88,True,0.84,
    'men+white+oxford+shirt+chinos+date+casual+night')

add("Black Leather Jacket & Jeans",
    "Edge and attitude — leather jacket over a tee with slim black jeans.",
    'male','date','fall','leather jacket','casual',
    ['black','white'],'solid','full',
    'Black Leather Jacket & White Tee','Stretch Black Jeans','Black Sneakers',
    [],['leather','cotton','denim'],
    ['slim','athletic'],0.84,True,0.90,
    'men+leather+jacket+black+jeans+date+night+edgy')

add("Navy Merino Knit & Dark Slacks",
    "Warm merino pullover with dark slim trousers — refined date night.",
    'male','date','winter','sweater','smart-casual',
    ['navy','charcoal'],'solid','full',
    'Fine Merino Knit Pullover','Dark Tailored Trousers','Brown Leather Loafers',
    [],['merino wool','wool'],
    ['average','slim','athletic'],0.87,False,0.80,
    'men+merino+navy+knit+pullover+date+night+smart')

add("Denim Shirt & Sandy Slim Chinos",
    "Casual denim shirt with slim sandy chinos — relaxed but intentional.",
    'male','date','spring','dress shirt','casual',
    ['blue','beige'],'solid','full',
    'Denim Button-Up Shirt (rolled cuffs)','Sandy Slim Chinos','White Sneakers',
    [],['denim','cotton'],
    ['all'],0.90,False,0.77,
    'men+denim+shirt+chinos+casual+date+day+romantic')

add("White Shirt & Dark Jeans Date Look",
    "Timeless white shirt with perfectly fitted dark jeans — always works.",
    'male','date','all','dress shirt','smart-casual',
    ['white','dark blue'],'solid','full',
    'Tailored White Shirt (untucked)','Dark Slim-Fit Jeans','Tan Sneakers',
    [],['cotton','denim'],
    ['all'],0.89,True,0.85,
    'men+white+shirt+dark+jeans+smart+casual+date+night')

# ═══════════════════════════════════════════════════════════════════════════
# FEMALE DATE
# ═══════════════════════════════════════════════════════════════════════════
add("Emerald Green Wrap Dress",
    "Elegant emerald wrap dress that flatters every silhouette for date nights.",
    'female','date','all','wrap dress','elegant',
    ['emerald','forest green'],'solid','half',
    'Emerald Wrap Dress (full)','N/A','Nude Heels',
    ['Gold Drop Earrings'],['chiffon','rayon'],
    ['hourglass','pear','rectangle'],0.83,True,0.91,
    'women+emerald+green+wrap+dress+date+night+elegant')

add("Fitted Black Mini Date Dress",
    "Classic LBD — cut close to the body for an irresistible silhouette.",
    'female','date','all','mini dress','elegant',
    ['black'],'solid','sleeveless',
    'Fitted Black Mini Dress (full)','N/A','Strappy Heels',
    ['Gold Hoop Earrings'],['polyester','crepe'],
    ['hourglass','pear'],0.78,True,0.90,
    'women+black+fitted+lbd+mini+dress+date+night')

add("Coral Off-Shoulder Floral Dress",
    "Romantic coral floral off-shoulder dress — perfect for dinner dates.",
    'female','date','spring','off-shoulder dress','feminine',
    ['coral','peach','pink'],'floral','sleeveless',
    'Off-Shoulder Floral Dress (full)','N/A','Strappy Sandals',
    ['Delicate Necklace'],['rayon','chiffon'],
    ['inverted_triangle','rectangle'],0.82,True,0.87,
    'women+coral+floral+off+shoulder+dress+date+romantic+spring')

add("Blush Satin Midi Skirt & Silk Blouse",
    "Luxurious satin slip skirt with silk blouse — effortlessly sensual.",
    'female','date','all','midi skirt','elegant',
    ['blush','rose','cream'],'solid','sleeveless',
    'Silk Blouse','Blush Satin Midi Skirt','Kitten Heels',
    ['Pearl Earrings'],['satin','silk'],
    ['hourglass','rectangle','inverted_triangle'],0.80,True,0.86,
    'women+satin+midi+skirt+silk+blouse+date+night+elegant')

add("Terracotta Boho Off-Shoulder Dress",
    "Free-spirited off-shoulder boho dress for relaxed romantic summer evenings.",
    'female','date','summer','off-shoulder dress','bohemian',
    ['terracotta','rust','cream'],'print','sleeveless',
    'Off-Shoulder Boho Dress (full)','N/A','Block Heel Sandals',
    ['Layered Necklace'],['cotton','rayon'],
    ['inverted_triangle','hourglass'],0.84,False,0.80,
    'women+terracotta+boho+off+shoulder+dress+date+summer')

add("Plum Velvet Midi Dress",
    "Deep plum velvet midi dress — mysterious and utterly chic for winter dates.",
    'female','date','fall','midi dress','elegant',
    ['deep purple','burgundy'],'solid','half',
    'Velvet Midi Dress (full)','N/A','Black Pumps',
    ['Gold Drop Earrings'],['velvet'],
    ['all'],0.77,True,0.88,
    'women+plum+velvet+midi+dress+date+night+winter+elegant')

add("Red Fitted Mini Date Dress",
    "Fierce red fitted mini — bold, unapologetic and impossible to forget.",
    'female','date','all','mini dress','glam',
    ['bright red','red'],'solid','sleeveless',
    'Fitted Red Mini Dress (full)','N/A','Nude Pointed Heels',
    ['Gold Ear Cuffs'],['polyester','crepe'],
    ['hourglass','rectangle'],0.75,True,0.92,
    'women+red+fitted+mini+dress+date+night+bold+sexy')

# ═══════════════════════════════════════════════════════════════════════════
# Validate count
# ═══════════════════════════════════════════════════════════════════════════
print(f"Total outfits defined: {len(OUTFITS)}")
assert len(OUTFITS) == 100, f"Expected 100 outfits, got {len(OUTFITS)}"
# Check all image URLs are unique
urls = [o['image_url'] for o in OUTFITS]
assert len(urls) == len(set(urls)), "Duplicate image URLs detected!"
print("✅ All 100 outfits have unique image URLs")

# ═══════════════════════════════════════════════════════════════════════════
# Database operations
# ═══════════════════════════════════════════════════════════════════════════
conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1. Add new columns (silently skip if already present)
for stmt in [
    "ALTER TABLE outfits ADD COLUMN category TEXT",
    "ALTER TABLE outfits ADD COLUMN pattern TEXT DEFAULT 'solid'",
    "ALTER TABLE outfits ADD COLUMN sleeve_type TEXT",
]:
    try:
        cur.execute(stmt)
        print(f"  Added column via: {stmt}")
    except Exception:
        pass  # column already exists

# 2. Wipe related tables (foreign key order)
for tbl in ('recommendations', 'user_feedbacks', 'outfit_interactions', 'outfits'):
    cur.execute(f"DELETE FROM {tbl}")
    print(f"  Cleared table: {tbl}")

# 3. Insert all 100 structured outfits
INSERT = """
INSERT INTO outfits (
    name, description, gender, occasion, season, category,
    style_type, colors, pattern, sleeve_type,
    top, bottom, shoes, accessories, fabric_types,
    body_type_compatibility, comfort_score, is_trending, trend_score, image_url
) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""
for o in OUTFITS:
    cur.execute(INSERT, (
        o['name'], o['description'], o['gender'], o['occasion'], o['season'],
        o['category'], o['style_type'],
        json.dumps(o['colors']), o['pattern'], o['sleeve_type'],
        o['top'], o['bottom'], o['shoes'],
        json.dumps(o['accessories']), json.dumps(o['fabric_types']),
        json.dumps(o['body_type_compatibility']),
        o['comfort_score'], 1 if o['is_trending'] else 0, o['trend_score'],
        o['image_url'],
    ))

conn.commit()
conn.close()

print(f"\n✅ Inserted {len(OUTFITS)} fully structured outfits")
print("   Attributes: name, gender, occasion, season, category, style_type,")
print("               colors, pattern, sleeve_type, body_type_compatibility")
print("   Images: unique per-outfit keywords via source.unsplash.com")
