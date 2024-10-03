import { createApp } from 'vue'
import App from './App.vue'
import './assets/tailwind.css'
createApp(App).mount('#app')


// npx tailwindcss -i ./src/assets/tailwind.css -o ./src/assets/output.css --watch