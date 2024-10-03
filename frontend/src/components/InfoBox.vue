<template>
    <div class="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
        <div class="flex items-center">
            <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd"
                        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                        clip-rule="evenodd" />
                </svg>
            </div>
            <div class="ml-3 flex-1">
                <p class="text-base md:text-lg text-blue-700">
                    <slot></slot>
                </p>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'InfoBox'
}
</script>
