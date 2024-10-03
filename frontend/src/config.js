// config.js
const ENV = process.env.NODE_ENV || 'development';

const CONFIG = {
    development: {
        ENDPOINT: 'http://127.0.0.1:8086'
    },
    production: {
        ENDPOINT: 'https://server.eviloder.win'
    }
};

export const ENDPOINT = CONFIG[ENV].ENDPOINT;