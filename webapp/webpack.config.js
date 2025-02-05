var path = require( 'path' );

module.exports = {
    entry: './src/app.jsx',
    output: {
        path: path.resolve( __dirname ),
        filename: './build/_bundle.js'
    },
    resolve: {
        extensions: ['.js', '.jsx']
    },
    module: {
        rules: [
            {
                test: /\.jsx$/,
                exclude: /node_modules/,
                use: { loader: 'babel-loader' }
            }
        ]
    }
};