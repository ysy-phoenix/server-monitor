// config.js
const ENV = process.env.NODE_ENV || 'development';

const CONFIG = {
    development: {
        ENDPOINT: 'http://127.0.0.1:8086'
    },
    production: {
        ENDPOINT: 'http://server.eviloder.win:8086' // 替换为您的生产环境 API 地址
    }
};

export const ENDPOINT = CONFIG[ENV].ENDPOINT;