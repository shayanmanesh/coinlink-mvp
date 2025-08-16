const webpack = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');

module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Production optimizations
      if (process.env.NODE_ENV === 'production') {
        // Enable aggressive code splitting
        webpackConfig.optimization = {
          ...webpackConfig.optimization,
          splitChunks: {
            chunks: 'all',
            cacheGroups: {
              vendor: {
                test: /[\\/]node_modules[\\/]/,
                name: 'vendors',
                priority: 10,
                reuseExistingChunk: true,
              },
              common: {
                minChunks: 2,
                priority: 5,
                reuseExistingChunk: true,
              },
            },
          },
          minimize: true,
          minimizer: [
            new TerserPlugin({
              terserOptions: {
                parse: {
                  ecma: 8,
                },
                compress: {
                  ecma: 5,
                  warnings: false,
                  comparisons: false,
                  inline: 2,
                  drop_console: true,
                  drop_debugger: true,
                },
                mangle: {
                  safari10: true,
                },
                output: {
                  ecma: 5,
                  comments: false,
                  ascii_only: true,
                },
              },
            }),
          ],
        };

        // Add compression plugin for gzip
        webpackConfig.plugins.push(
          new CompressionPlugin({
            algorithm: 'gzip',
            test: /\.(js|css|html|svg)$/,
            threshold: 8192,
            minRatio: 0.8,
          })
        );

        // Define production environment variables
        webpackConfig.plugins.push(
          new webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify('production'),
            'process.env.REACT_APP_API_URL': JSON.stringify(process.env.REACT_APP_API_URL || 'https://api.coin.link'),
            'process.env.REACT_APP_WS_URL': JSON.stringify(process.env.REACT_APP_WS_URL || 'wss://api.coin.link'),
          })
        );
      }

      return webpackConfig;
    },
  },
};