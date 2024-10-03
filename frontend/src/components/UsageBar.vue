<template>
    <div class="mb-4">
        <div class="flex justify-between items-center mb-2">
            <span class="text-gray-600">{{ label }}:</span>
            <span class="font-medium" :class="textColor">{{ usage.toFixed(2) }}%</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2.5">
            <div class="h-2.5 rounded-full" :class="barColor" :style="{ width: `${usage}%` }"></div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        label: {
            type: String,
            required: true,
        },
        usage: {
            type: Number,
            required: true,
        },
    },
    computed: {
        textColor() {
            if (this.usage < 50) return 'text-green-500';
            if (this.usage < 80) return 'text-yellow-500';
            return 'text-red-500';
        },
        barColor() {
            if (this.usage < 50) return 'bg-green-500';
            if (this.usage < 80) return 'bg-yellow-500';
            return 'bg-red-500';
        },
    },
}
</script>