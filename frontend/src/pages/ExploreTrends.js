import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiArrowLeft, FiArrowRight, FiTrendingUp } from 'react-icons/fi';
import { HiOutlineSparkles } from 'react-icons/hi';

// ─── Static trend data ────────────────────────────────────────────────────────

const MEN_TRENDS = [
  {
    id: 'm1',
    name: 'Minimalist Casual Wear',
    category: "Men's Casual",
    description: 'Clean lines and neutral palettes for effortless, everyday elegance. Less is unmistakably more.',
    image: 'https://images.unsplash.com/photo-1488161628813-04466f872be2?q=80&w=600',
  },
  {
    id: 'm2',
    name: 'Streetwear Style',
    category: "Men's Streetwear",
    description: 'Bold graphics, oversized silhouettes, and raw urban-inspired aesthetics straight from the block.',
    image: 'https://images.unsplash.com/photo-1509631179647-0177331693ae?q=80&w=600',
  },
  {
    id: 'm3',
    name: 'Smart Casual Outfits',
    category: "Men's Smart Casual",
    description: 'Elevated everyday looks where formal precision meets relaxed comfort for any occasion.',
    image: 'https://images.unsplash.com/photo-1617137968427-85924c800a22?q=80&w=600',
  },
  {
    id: 'm4',
    name: 'Athleisure Fashion',
    category: "Men's Athletic",
    description: 'Performance-inspired looks engineered for unrestricted movement and modern street appeal.',
    image: 'https://images.unsplash.com/photo-1571945153237-4929e783af4a?q=80&w=600',
  },
  {
    id: 'm5',
    name: 'Formal Business Looks',
    category: "Men's Formal",
    description: 'Sharp, tailored suits and polished professional attire that command presence and respect.',
    image: 'https://images.unsplash.com/photo-1490578474895-699cd4e2cf59?q=80&w=600',
  },
];

const WOMEN_TRENDS = [
  {
    id: 'w1',
    name: 'Summer Dresses',
    category: "Women's Summer",
    description: 'Breezy, light designs in flowing fabrics that transition effortlessly from beach to brunch.',
    image: 'https://images.unsplash.com/photo-1496747611176-843222e1e57c?q=80&w=600',
  },
  {
    id: 'w2',
    name: 'Minimalist Fashion',
    category: "Women's Minimal",
    description: 'Refined simplicity — carefully chosen pieces that express confidence without speaking loudly.',
    image: 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?q=80&w=600',
  },
  {
    id: 'w3',
    name: 'Bohemian Style',
    category: "Women's Boho",
    description: 'Free-spirited patterns, flowing fabrics, and layered artisan accessories celebrating individuality.',
    image: 'https://images.unsplash.com/photo-1469334031218-e382a71b716b?q=80&w=600',
  },
  {
    id: 'w4',
    name: 'Office Chic',
    category: "Women's Formal",
    description: 'Sophisticated power dressing that commands the room while remaining effortlessly modern.',
    image: 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?q=80&w=600',
  },
  {
    id: 'w5',
    name: 'Party Wear',
    category: "Women's Glam",
    description: 'Glamorous evening looks crafted for special occasions and the nights you will never forget.',
    image: 'https://images.unsplash.com/photo-1566174053879-31528523f8ae?q=80&w=600',
  },
];

const SEASONAL_TRENDS = [
  {
    season: 'Summer Fashion',
    icon: '☀️',
    tagline: 'Light fabrics · Pastel palettes · Breathable silhouettes',
    description:
      'Cotton, linen and chambray dominate summer 2026. Pastels paired with crisp whites build the quintessential warm-season wardrobe that moves from morning market runs to rooftop evenings.',
    fabrics: ['Cotton', 'Linen', 'Chambray', 'Seersucker'],
    colors: [
      { name: 'Pastel Blue', hex: '#AED6F1' },
      { name: 'Coral',       hex: '#F1948A' },
      { name: 'Ivory',       hex: '#FAF9F0' },
      { name: 'Mint',        hex: '#A9DFBF' },
    ],
    outfits: [
      {
        image: 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?q=80&w=400',
        name: 'Linen Casual',
        desc: 'Lightweight linen cuts for sun-drenched afternoons',
      },
      {
        image: 'https://images.unsplash.com/photo-1485968579580-b6d095142e6e?q=80&w=400',
        name: 'Pastel Edit',
        desc: 'Soft tones that glow in warm natural light',
      },
      {
        image: 'https://images.unsplash.com/photo-1469334031218-e382a71b716b?q=80&w=400',
        name: 'Resort Chic',
        desc: 'Effortless resort-ready elegance in every piece',
      },
    ],
  },
  {
    season: 'Winter Fashion',
    icon: '❄️',
    tagline: 'Luxurious layers · Statement coats · Rich deep palettes',
    description:
      'Cashmere, wool and velvet define winter 2026. Deep navy, burgundy and charcoal anchor a rich palette of warmth, with statement outerwear serving as the focal point of every look.',
    fabrics: ['Cashmere', 'Wool', 'Velvet', 'Fleece'],
    colors: [
      { name: 'Deep Navy', hex: '#1B2631' },
      { name: 'Burgundy',  hex: '#7B241C' },
      { name: 'Charcoal',  hex: '#2C3E50' },
      { name: 'Camel',     hex: '#C19A6B' },
    ],
    outfits: [
      {
        image: 'https://images.unsplash.com/photo-1605763240000-7e93b172d754?q=80&w=400',
        name: 'Winter Layers',
        desc: 'Cozy stacked layers that defy the cold in style',
      },
      {
        image: 'https://images.unsplash.com/photo-1483985988355-763728e1935b?q=80&w=400',
        name: 'Statement Coat',
        desc: 'Bold outerwear chosen to be the entire conversation',
      },
      {
        image: 'https://images.unsplash.com/photo-1512436991641-6745cdb1723f?q=80&w=400',
        name: 'Knit & Tuck',
        desc: 'Elevated knitwear anchored by structured bottoms',
      },
    ],
  },
];

const COLOR_TRENDS = [
  {
    name: 'Neutral Minimalism',
    description:
      'Beige, white, and cream tones that create a timeless, effortless aesthetic — clothing that lets your personality take centre stage.',
    palette: [
      { hex: '#F5F0E8', name: 'Cream' },
      { hex: '#E8D5B7', name: 'Sand' },
      { hex: '#C4A882', name: 'Linen' },
      { hex: '#8B7355', name: 'Camel' },
      { hex: '#5C4A32', name: 'Taupe' },
    ],
    styles: ['Minimalist Casual', 'Smart Casual', 'Business Casual'],
    image: 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=700',
  },
  {
    name: 'Bold Statement Colors',
    description:
      'Red, royal blue, and emerald for powerful, confident dressing. These high-impact hues are made for those who refuse to go unnoticed.',
    palette: [
      { hex: '#C0392B', name: 'Crimson'    },
      { hex: '#1A5276', name: 'Royal Blue' },
      { hex: '#1E8449', name: 'Emerald'    },
      { hex: '#D4AC0D', name: 'Gold'       },
      { hex: '#4A235A', name: 'Violet'     },
    ],
    styles: ['Party Wear', 'Evening Glam', 'Power Dressing'],
    image: 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=700',
  },
  {
    name: 'Earthy Natural Colors',
    description:
      'Olive, rust, and mustard that ground fashion in the warmth of nature — organic, lived-in, and unmistakably sophisticated.',
    palette: [
      { hex: '#556B2F', name: 'Olive'       },
      { hex: '#B7410E', name: 'Rust'        },
      { hex: '#E3A857', name: 'Mustard'     },
      { hex: '#8B4513', name: 'Saddle Brown'},
      { hex: '#8FBC8F', name: 'Sage'        },
    ],
    styles: ['Bohemian', 'Resort Wear', 'Casual'],
    image: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=700',
  },
];

// ─── Small reusable components ────────────────────────────────────────────────

const SectionHeader = ({ title, subtitle }) => (
  <div className="mb-10">
    <div className="flex items-center gap-5 mb-3">
      <h2 className="text-3xl font-bold text-gray-900 tracking-tight whitespace-nowrap">{title}</h2>
      <div className="h-px flex-1 bg-gradient-to-r from-amber-600 to-transparent" />
    </div>
    {subtitle && <p className="text-gray-500 font-light">{subtitle}</p>}
  </div>
);

const TrendCard = ({ image, name, category, description, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 30 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ duration: 0.5, delay }}
    className="bg-white border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow group"
  >
    <div className="h-56 overflow-hidden bg-gray-100">
      <img
        src={image}
        alt={name}
        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
      />
    </div>
    <div className="p-5">
      <span className="text-xs font-bold text-amber-600 tracking-widest uppercase">{category}</span>
      <h4 className="text-lg font-bold text-gray-900 mt-1 mb-2">{name}</h4>
      <p className="text-gray-500 text-sm font-light leading-relaxed">{description}</p>
    </div>
  </motion.div>
);

// ─── Main page ────────────────────────────────────────────────────────────────

const ExploreTrends = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ── Hero ── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1 }}
        className="relative text-white overflow-hidden"
        style={{
          backgroundImage:
            'url(https://images.unsplash.com/photo-1558618666-fcd25c85cd64?q=80&w=2070)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-black/90 via-black/75 to-black/65" />
        <div className="absolute top-10 right-10 w-64 h-64 bg-amber-600 opacity-10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-10 left-10 w-96 h-96 bg-amber-500 opacity-5 rounded-full blur-3xl" />

        <div className="relative z-10 container mx-auto px-6 py-20">
          {/* Back link */}
          <motion.button
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            onClick={() => navigate('/trends')}
            className="flex items-center gap-2 text-gray-300 hover:text-white text-sm tracking-wide mb-10 transition-colors"
          >
            <FiArrowLeft />
            Back to Trends
          </motion.button>

          <motion.div
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="max-w-3xl mx-auto text-center"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="inline-block mb-6"
            >
              <FiTrendingUp className="text-6xl text-amber-500 mx-auto drop-shadow-lg" />
            </motion.div>

            <h1 className="text-5xl font-bold mb-5 tracking-tight drop-shadow-lg">
              Fashion Trends Explorer
            </h1>
            <div className="w-20 h-1 bg-amber-600 mx-auto mb-5" />
            <p className="text-xl text-gray-200 font-light leading-relaxed drop-shadow-md">
              Discover modern outfit styles, seasonal collections, and inspiring color palettes — your
              guide to understanding what's shaping fashion in 2026.
            </p>
          </motion.div>
        </div>
      </motion.div>

      {/* ── Quick navigation ── */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-20 shadow-sm">
        <div className="container mx-auto px-6">
          <div className="flex gap-8 overflow-x-auto py-4 text-sm font-medium tracking-wide uppercase text-gray-500 scrollbar-hide">
            {[
              { label: "Men's Styles",     href: '#mens'    },
              { label: "Women's Styles",   href: '#womens'  },
              { label: 'Seasonal Trends',  href: '#seasonal'},
              { label: 'Color Trends',     href: '#colors'  },
            ].map(({ label, href }) => (
              <a
                key={href}
                href={href}
                className="whitespace-nowrap hover:text-amber-600 transition-colors"
              >
                {label}
              </a>
            ))}
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-16 space-y-24">

        {/* ── Men's Trending Styles ── */}
        <section id="mens">
          <SectionHeader
            title="Men's Trending Styles"
            subtitle="Popular outfit combinations shaping men's fashion right now — from minimalist everyday looks to sharp formal wear."
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            {MEN_TRENDS.map((t, i) => (
              <TrendCard key={t.id} {...t} delay={i * 0.08} />
            ))}
          </div>
        </section>

        {/* ── Women's Trending Styles ── */}
        <section id="womens">
          <SectionHeader
            title="Women's Trending Styles"
            subtitle="Modern fashion trends popular among women — from effortless summer dresses to powerful office looks and glamorous evening wear."
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            {WOMEN_TRENDS.map((t, i) => (
              <TrendCard key={t.id} {...t} delay={i * 0.08} />
            ))}
          </div>
        </section>

        {/* ── Seasonal Fashion Trends ── */}
        <section id="seasonal">
          <SectionHeader
            title="Seasonal Fashion Trends"
            subtitle="Understand how fashion evolves with the seasons — the fabrics, palettes, and silhouettes that define each time of year."
          />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
            {SEASONAL_TRENDS.map((season, si) => (
              <motion.div
                key={season.season}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: si * 0.15 }}
                className="bg-white border border-gray-200 overflow-hidden shadow-sm"
              >
                {/* Season header */}
                <div className="bg-gray-900 text-white px-7 py-5">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-2xl">{season.icon}</span>
                    <h3 className="text-xl font-bold tracking-tight">{season.season}</h3>
                  </div>
                  <p className="text-amber-400 text-xs tracking-widest uppercase font-medium">
                    {season.tagline}
                  </p>
                </div>

                <div className="p-7">
                  <p className="text-gray-600 text-sm font-light leading-relaxed mb-6">
                    {season.description}
                  </p>

                  {/* Fabric tags */}
                  <div className="mb-5">
                    <p className="text-xs font-bold text-gray-400 tracking-widest uppercase mb-2">Key Fabrics</p>
                    <div className="flex flex-wrap gap-2">
                      {season.fabrics.map((f) => (
                        <span
                          key={f}
                          className="text-xs px-3 py-1 bg-gray-100 text-gray-700 font-medium tracking-wide"
                        >
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Color chips */}
                  <div className="mb-7">
                    <p className="text-xs font-bold text-gray-400 tracking-widest uppercase mb-3">Trending Palette</p>
                    <div className="flex gap-3">
                      {season.colors.map((c) => (
                        <div key={c.name} className="text-center">
                          <div
                            className="w-10 h-10 border border-gray-200 shadow-sm mb-1"
                            style={{ backgroundColor: c.hex }}
                          />
                          <p className="text-xs text-gray-500 font-medium leading-tight">{c.name}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Outfit mini-cards */}
                  <p className="text-xs font-bold text-gray-400 tracking-widest uppercase mb-3">Style Examples</p>
                  <div className="grid grid-cols-3 gap-3">
                    {season.outfits.map((o, oi) => (
                      <motion.div
                        key={o.name}
                        initial={{ opacity: 0, scale: 0.92 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                        transition={{ delay: si * 0.1 + oi * 0.1 }}
                        className="group"
                      >
                        <div className="h-28 overflow-hidden bg-gray-100 mb-2">
                          <img
                            src={o.image}
                            alt={o.name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                          />
                        </div>
                        <p className="text-xs font-semibold text-gray-800">{o.name}</p>
                        <p className="text-xs text-gray-400 font-light leading-snug">{o.desc}</p>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ── Color Trend Inspirations ── */}
        <section id="colors">
          <SectionHeader
            title="Color Trend Inspirations"
            subtitle="The palettes defining fashion in 2026 — understand which color families are trending and how to wear them confidently."
          />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {COLOR_TRENDS.map((ct, ci) => (
              <motion.div
                key={ct.name}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: ci * 0.15 }}
                className="bg-white border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow group"
              >
                {/* Hero image */}
                <div className="h-52 overflow-hidden bg-gray-100">
                  <img
                    src={ct.image}
                    alt={ct.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                </div>

                <div className="p-6">
                  <h4 className="text-xl font-bold text-gray-900 mb-2 tracking-tight">{ct.name}</h4>
                  <p className="text-gray-500 text-sm font-light leading-relaxed mb-5">
                    {ct.description}
                  </p>

                  {/* Colour swatches */}
                  <div className="flex gap-2 mb-5">
                    {ct.palette.map((swatch) => (
                      <div key={swatch.name} className="text-center group/swatch relative">
                        <div
                          className="w-9 h-9 border border-gray-200 shadow-sm cursor-default"
                          style={{ backgroundColor: swatch.hex }}
                          title={swatch.name}
                        />
                        {/* Tooltip */}
                        <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-0.5 opacity-0 group-hover/swatch:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                          {swatch.name}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Style tags */}
                  <div className="flex flex-wrap gap-2">
                    {ct.styles.map((s) => (
                      <span
                        key={s}
                        className="text-xs px-3 py-1 bg-amber-50 text-amber-700 font-medium tracking-wide"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ── CTA ── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="bg-gray-900 text-white p-12 text-center relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 w-64 h-64 bg-amber-600 opacity-10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-amber-500 opacity-5 rounded-full blur-3xl" />
          <div className="relative z-10">
            <HiOutlineSparkles className="text-5xl text-amber-500 mx-auto mb-5" />
            <h2 className="text-3xl font-bold tracking-tight mb-4">
              Ready to Find Your Perfect Style?
            </h2>
            <p className="text-gray-300 font-light max-w-xl mx-auto mb-8 leading-relaxed">
              Now that you've explored the latest trends, let our AI generate outfit recommendations
              tailored specifically to your body type, skin tone, and personal preferences.
            </p>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate('/recommendations')}
              className="inline-flex items-center gap-3 bg-amber-600 text-white px-10 py-4 font-medium text-sm tracking-widest uppercase hover:bg-amber-700 transition-colors"
            >
              <HiOutlineSparkles />
              Get Personalized Recommendations
              <FiArrowRight />
            </motion.button>
          </div>
        </motion.div>

      </div>
    </div>
  );
};

export default ExploreTrends;
