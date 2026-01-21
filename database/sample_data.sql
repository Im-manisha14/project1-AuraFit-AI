-- Sample data for testing StyleSync platform

-- Sample outfits
INSERT INTO outfits (name, description, top, bottom, shoes, occasion, season, style_type, colors, fabric_types, comfort_score, is_trending, trend_score) VALUES
('Classic Business Suit', 'Professional navy suit perfect for business meetings', 'Blazer', 'Dress Pants', 'Oxford Shoes', 'work', 'all', 'formal', '["navy", "white"]', '["wool", "cotton"]', 0.7, false, 0.6),
('Summer Breeze Outfit', 'Light and airy summer casual wear', 'Linen Shirt', 'Shorts', 'Sandals', 'casual', 'summer', 'casual', '["white", "beige"]', '["linen", "cotton"]', 0.9, true, 0.85),
('Athleisure Chic', 'Trendy athletic-inspired casual wear', 'Crop Top', 'Leggings', 'Sneakers', 'gym', 'all', 'sporty', '["black", "purple"]', '["spandex", "polyester"]', 0.95, true, 0.92),
('Elegant Evening Dress', 'Sophisticated black dress for formal events', 'Evening Dress', 'N/A', 'Heels', 'party', 'all', 'formal', '["black"]', '["silk", "satin"]', 0.6, true, 0.8),
('Cozy Winter Layers', 'Warm and stylish winter outfit', 'Sweater', 'Jeans', 'Boots', 'casual', 'winter', 'casual', '["gray", "navy"]', '["wool", "denim"]', 0.85, false, 0.65),
('Boho Festival Look', 'Free-spirited bohemian style', 'Flowy Top', 'Maxi Skirt', 'Sandals', 'party', 'summer', 'bohemian', '["terracotta", "cream"]', '["cotton", "rayon"]', 0.8, true, 0.75),
('Smart Casual Friday', 'Perfect balance of professional and relaxed', 'Polo Shirt', 'Chinos', 'Loafers', 'work', 'all', 'smart-casual', '["navy", "khaki"]', '["cotton", "cotton"]', 0.8, false, 0.7),
('Date Night Elegance', 'Romantic and sophisticated outfit', 'Blouse', 'Pencil Skirt', 'Heels', 'date', 'all', 'elegant', '["red", "black"]', '["silk", "polyester"]', 0.65, true, 0.82),
('Minimalist Modern', 'Clean lines and neutral tones', 'Turtleneck', 'Wide Pants', 'Sneakers', 'casual', 'fall', 'minimalist', '["beige", "white"]', '["cotton", "linen"]', 0.88, true, 0.88),
('Spring Pastels', 'Soft and refreshing spring colors', 'Cardigan', 'Dress', 'Flats', 'casual', 'spring', 'feminine', '["lavender", "pink"]', '["cotton", "rayon"]', 0.82, true, 0.79);

-- You can add more sample data as needed
