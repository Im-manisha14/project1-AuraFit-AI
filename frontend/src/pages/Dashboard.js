import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { outfitAPI } from '../services/api';
import { motion } from 'framer-motion';
import { FiTrendingUp, FiStar, FiArrowRight, FiShoppingBag } from 'react-icons/fi';
import { HiOutlineSparkles } from 'react-icons/hi';

const Dashboard = () => {
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const trendingRes = await outfitAPI.getTrending(6);
      setTrending(trendingRes.data.outfits || []);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setTrending([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-amber-600 mx-auto mb-4"></div>
          <p className="text-gray-700 font-medium">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white overflow-hidden">
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1 }}
        className="relative bg-gray-900 text-white overflow-hidden"
      >
        <motion.div 
          initial={{ scale: 1.2 }}
          animate={{ scale: 1 }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          className="absolute inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-black"
        />
        
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.6 }}
          transition={{ duration: 1.2 }}
          className="absolute inset-0 bg-black z-10"
        />
        
        <div className="relative z-20 container mx-auto px-6 py-32 text-center">
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <div className="inline-block mb-6">
              <HiOutlineSparkles className="text-5xl text-amber-500 mx-auto" />
            </div>
            <h1 className="text-6xl font-bold mb-8 tracking-tight">
              HIGH-END & CLASSY
            </h1>
          </motion.div>
          
          <motion.p 
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-xl mb-12 font-light max-w-2xl mx-auto leading-relaxed"
          >
            Experience luxury fashion with AI-powered personalized styling
          </motion.p>
          
          <motion.div 
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="flex justify-center space-x-6"
          >
            <Link 
              to="/trends" 
              className="group border border-white text-white px-8 py-4 font-medium text-sm tracking-widest uppercase hover:bg-white hover:text-gray-900 transition-all duration-300 flex items-center space-x-2"
            >
              <span>Learn More</span>
              <FiArrowRight className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link 
              to="/recommendations" 
              className="group bg-amber-600 text-white px-8 py-4 font-medium text-sm tracking-widest uppercase hover:bg-amber-700 transition-all duration-300 flex items-center space-x-2"
            >
              <FiShoppingBag />
              <span>Start Now</span>
            </Link>
          </motion.div>
        </div>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.8 }}
        className="bg-gray-50 py-16"
      >
        <div className="container mx-auto px-6">
          <motion.h2 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-3xl font-bold text-center text-gray-900 mb-12 tracking-tight"
          >
            Our Signature Palette
          </motion.h2>
          
          <div className="grid grid-cols-4 gap-8 max-w-4xl mx-auto">
            {[
              { color: 'bg-amber-700', name: 'Amber Gold' },
              { color: 'bg-gray-800', name: 'Charcoal' },
              { color: 'bg-gray-100', name: 'Pearl' },
              { color: 'bg-gray-600', name: 'Graphite' }
            ].map((item, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="text-center"
              >
                <div className={`${item.color} h-32 mb-4 shadow-md hover:scale-105 transition-transform`}></div>
                <p className="text-gray-900 font-medium">{item.name}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 1 }}
        className="bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white py-24 relative overflow-hidden"
      >
        {/* Decorative background elements */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-amber-600 opacity-5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-amber-600 opacity-5 rounded-full blur-3xl"></div>
        
        <div className="container mx-auto px-6 relative z-10">
          <div className="grid md:grid-cols-2 gap-20 items-center max-w-6xl mx-auto">
            <motion.div
              initial={{ x: -50, opacity: 0 }}
              whileInView={{ x: 0, opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
            >
              <motion.div 
                initial={{ width: 0 }}
                whileInView={{ width: "60px" }}
                viewport={{ once: true }}
                transition={{ duration: 0.8, delay: 0.2 }}
                className="h-1 bg-gradient-to-r from-amber-600 to-amber-400 mb-8"
              ></motion.div>
              
              <h2 className="text-5xl font-bold mb-8 tracking-tight leading-tight">
                Luxurious & Distinctive
              </h2>
              
              <p className="text-gray-300 leading-relaxed mb-6 text-lg font-light">
                AuraFit combines cutting-edge AI technology with timeless elegance to deliver personalized fashion recommendations that reflect your unique style.
              </p>
              
              <p className="text-gray-300 leading-relaxed text-lg font-light mb-8">
                Every recommendation is crafted with precision, ensuring you always look your absolute best.
              </p>
              
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.4 }}
                className="flex items-center space-x-2 text-amber-500"
              >
                <div className="w-12 h-px bg-amber-500"></div>
                <span className="text-sm tracking-widest uppercase">Excellence in Every Detail</span>
              </motion.div>
            </motion.div>
            
            <motion.div
              initial={{ x: 50, opacity: 0 }}
              whileInView={{ x: 0, opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
              className="grid grid-cols-2 gap-6"
            >
              {[
                { icon: FiTrendingUp, label: 'Trend Analysis', desc: 'Stay ahead of fashion curves' },
                { icon: FiStar, label: 'Premium Quality', desc: 'Curated excellence' },
                { icon: FiShoppingBag, label: 'Curated Collections', desc: 'Handpicked selections' },
                { icon: HiOutlineSparkles, label: 'AI-Powered', desc: 'Intelligent recommendations' }
              ].map((item, index) => (
                <motion.div 
                  key={index}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  whileHover={{ y: -10, scale: 1.05 }}
                  className="bg-white bg-opacity-5 backdrop-blur-sm p-8 text-center border border-white border-opacity-10 hover:border-amber-500 hover:border-opacity-50 transition-all duration-300 group"
                >
                  <motion.div
                    whileHover={{ rotate: 360 }}
                    transition={{ duration: 0.6 }}
                  >
                    <item.icon className="text-4xl text-amber-500 mx-auto mb-4 group-hover:text-amber-400 transition-colors" />
                  </motion.div>
                  <p className="text-white font-semibold text-base mb-2">{item.label}</p>
                  <p className="text-gray-400 text-xs font-light">{item.desc}</p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Dashboard;
