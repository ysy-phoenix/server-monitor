<template>
    <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 font-sans">
        <div class="container mx-auto max-w-7xl px-4">
            <h1 class="text-6xl font-bold text-gray-800 mb-12 text-center font-serif">BDAA 服务器状态</h1>
            <InfoBox class="mb-8">
                每 20 分钟更新一次数据，每次更新约 20 秒。
            </InfoBox>

            <!-- 加载状态 -->
            <div v-if="isLoading" class="flex justify-center items-center h-64">
                <div class="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-blue-500"></div>
            </div>

            <div v-else>
                <!-- 服务器状态卡片 -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
                    <div v-for="server in servers" :key="server.name"
                        class="bg-white rounded-xl shadow-lg overflow-hidden transform transition duration-300 hover:scale-105">
                        <div class="bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-5">
                            <h2 class="text-3xl font-bold text-white">{{ server.name }}</h2>
                        </div>
                        <div class="p-6">
                            <!-- CPU 使用率 -->
                            <div class="mb-6">
                                <h3 class="text-2xl font-semibold text-gray-800 mb-4 font-serif">CPU 状态</h3>
                                <UsageBar label="CPU 使用率" :usage="server.cpu_usage" class="mb-3" />
                                <UsageBar label="CPU 内存使用率" :usage="server.cpu_memory_usage" />
                            </div>

                            <!-- GPU 使用率 -->
                            <div>
                                <h3 class="text-2xl font-semibold text-gray-800 mb-4 font-serif">GPU 状态</h3>
                                <div class="grid grid-cols-2 gap-5">
                                    <div v-for="(gpu, index) in server.gpus" :key="index"
                                        class="bg-gray-50 rounded-lg p-4 shadow-inner">
                                        <h4 class="text-xl font-medium text-gray-700 mb-3">GPU {{ gpu.index }}</h4>
                                        <UsageBar label="使用率" :usage="gpu.usage" class="mb-3" />
                                        <UsageBar label="内存使用率" :usage="gpu.memory_usage" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 历史记录 -->
                <div class="bg-white rounded-xl shadow-lg overflow-hidden mb-12">
                    <div class="bg-gradient-to-r from-green-600 to-teal-700 px-6 py-5">
                        <h2 class="text-4xl font-bold text-white">违规历史记录</h2>
                    </div>
                    <div class="p-6">
                        <!-- CPU 历史记录 -->
                        <div class="mb-12">
                            <h3 class="text-3xl font-semibold text-gray-800 mb-6">CPU 违规使用记录</h3>
                            <InfoBox class="mb-8">
                                CPU 违规为每台机器使用 CPU 核数超过 1 / 4，仅显示使用率超过 90% 的记录，数据仅存七天。
                            </InfoBox>
                            <!-- 筛选器 -->
                            <div class="mb-6 flex flex-wrap gap-4">
                                <input v-model="cpuFilters.startDate" type="date" @input="filterCpuHistory"
                                    placeholder="起始日期" class="input">
                                <input v-model="cpuFilters.endDate" type="date" @input="filterCpuHistory"
                                    placeholder="结束日期" class="input">
                                <input v-model="cpuFilters.server" @input="filterCpuHistory" placeholder="服务器筛选"
                                    class="input">
                                <input v-model="cpuFilters.user" @input="filterCpuHistory" placeholder="用户筛选"
                                    class="input">
                                <!-- 添加去重按钮 -->
                                <button @click="toggleCpuDeduplication" class="btn"
                                    :class="{ 'bg-green-500': isCpuDeduplicating }">
                                    {{ isCpuDeduplicating ? '取消去重' : '去重' }}
                                </button>
                            </div>
                            <div class="overflow-x-auto">
                                <table class="min-w-full bg-white border border-gray-300 rounded-lg overflow-hidden">
                                    <thead class="bg-gray-100">
                                        <tr>
                                            <th @click="sortCpuHistory('timestamp')" class="table-header" style="white-space: nowrap;">
                                                日期 <span v-if="cpuSortKey === 'timestamp'">{{ cpuSortOrder === 'asc' ?
                                                    '▲' : '▼' }}</span>
                                            </th>
                                            <th @click="sortCpuHistory('name')" class="table-header" style="white-space: nowrap;">
                                                服务器 <span v-if="cpuSortKey === 'name'">{{ cpuSortOrder === 'asc' ? '▲' :
                                                    '▼' }}</span>
                                            </th>
                                            <th @click="sortCpuHistory('user')" class="table-header" style="white-space: nowrap;">
                                                用户 <span v-if="cpuSortKey === 'user'">{{ cpuSortOrder === 'asc' ? '▲' :
                                                    '▼' }}</span>
                                            </th>
                                            <th class="table-header">使用率</th>
                                            <th class="table-header">命令</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-gray-200">
                                        <template v-for="(group, groupIndex) in groupedCpuHistory" :key="groupIndex">
                                            <tr v-for="(record, recordIndex) in group.records" :key="record.id"
                                                class="hover:bg-gray-50">
                                                <td v-if="recordIndex === 0" :rowspan="group.records.length"
                                                    class="table-cell font-medium" v-html="formatDate(group.timestamp)">
                                                </td>
                                                <td v-if="recordIndex === 0" :rowspan="group.records.length"
                                                    class="table-cell">{{ group.name }}</td>
                                                <td v-if="recordIndex === 0" :rowspan="group.records.length"
                                                    class="table-cell">{{ group.user }}</td>
                                                <td class="table-cell font-medium" :class="getUsageColor(record.usage)">
                                                    {{ record.usage.toFixed(2) }}%</td>
                                                <td class="table-cell">{{ record.command }}</td>
                                            </tr>
                                        </template>
                                    </tbody>
                                </table>
                            </div>
                            <!-- 分页控件 -->
                            <div class="mt-6 flex justify-between items-center">
                                <button @click="prevCpuPage" :disabled="cpuCurrentPage === 1" class="btn">上一页</button>
                                <span class="text-gray-600">
                                    第 <input v-model.number="cpuCurrentPage" @change="goToCpuPage" type="number"
                                        class="w-16 px-2 py-1 border rounded text-center"> 页，共 {{ cpuTotalPages }} 页
                                </span>
                                <span class="text-gray-600">
                                    每页条数：
                                    <input v-model.number="cpuItemsPerPage"
                                        @input="cpuItemsPerPage = validateItemsPerPage($event.target.value)"
                                        type="number" min="1" class="w-20 px-2 py-1 border rounded text-center"
                                        placeholder="每页条数">
                                </span>
                                <button @click="nextCpuPage" :disabled="cpuCurrentPage === cpuTotalPages"
                                    class="btn">下一页</button>
                            </div>
                        </div>

                        <!-- GPU 历史记录 -->
                        <div class="mt-12">
                            <h3 class="text-3xl font-semibold text-gray-800 mb-6">GPU 违规使用记录</h3>
                            <InfoBox class="mb-6">
                                背景为浅黄色表示该用户同时使用了两张以上的显卡；背景为浅红色表示存在高显存占用但低利用率的情况；数据仅存七天。
                            </InfoBox>
                            <!-- 筛选器 -->
                            <div class="mb-6 flex flex-wrap gap-4">
                                <input v-model="gpuFilters.startDate" type="date" @input="filterGpuHistory"
                                    placeholder="起始日期" class="input">
                                <input v-model="gpuFilters.endDate" type="date" @input="filterGpuHistory"
                                    placeholder="结束日期" class="input">
                                <input v-model="gpuFilters.server" @input="filterGpuHistory" placeholder="服务器筛选"
                                    class="input">
                                <input v-model="gpuFilters.user" @input="filterGpuHistory" placeholder="用户筛选"
                                    class="input">
                                <input v-model="gpuFilters.error" @input="filterGpuHistory" placeholder="错误筛选"
                                    class="input">
                                <!-- 添加去重按钮 -->
                                <button @click="toggleGpuDeduplication" class="btn"
                                    :class="{ 'bg-green-500': isGpuDeduplicating }">
                                    {{ isGpuDeduplicating ? '取消去重' : '去重' }}
                                </button>
                            </div>
                            <div class="overflow-x-auto">
                                <table class="min-w-full bg-white border border-gray-300 rounded-lg overflow-hidden">
                                    <thead class="bg-gray-100">
                                        <tr>
                                            <th @click="sortGpuHistory('timestamp')" class="table-header">
                                                日期 <span v-if="gpuSortKey === 'timestamp'">{{ gpuSortOrder === 'asc' ?
                                                    '▲' : '▼' }}</span>
                                            </th>
                                            <th @click="sortGpuHistory('name')" class="table-header">
                                                服务器 <span v-if="gpuSortKey === 'name'">{{ gpuSortOrder === 'asc' ? '▲' :
                                                    '▼' }}</span>
                                            </th>
                                            <th @click="sortGpuHistory('user')" class="table-header">
                                                用户 <span v-if="gpuSortKey === 'user'">{{ gpuSortOrder === 'asc' ? '▲' :
                                                    '▼' }}</span>
                                            </th>
                                            <th @click="sortGpuHistory('error')" class="table-header"
                                                style="white-space: nowrap;">
                                                非法 <span v-if="gpuSortKey === 'error'">{{ gpuSortOrder === 'asc' ? '▲' :
                                                    '▼' }}</span>
                                            </th>
                                            <th class="table-header" style="white-space: nowrap;">索引</th>
                                            <th class="table-header" style="white-space: nowrap;">SM</th>
                                            <th class="table-header" style="white-space: nowrap;">MEM</th>
                                            <th class="table-header" style="white-space: nowrap;">显存</th>
                                            <th class="table-header" style="white-space: nowrap;">命令</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-gray-200">
                                        <template v-for="(group, groupIndex) in groupedGpuHistory" :key="groupIndex">
                                            <tr v-for="(record, recordIndex) in group.records" :key="record.id" :class="[
                                                { 'bg-yellow-50': group.error === 0, 'bg-red-50': group.error === 1 }
                                            ]">
                                                <td v-if="recordIndex === 0" :rowspan="group.records.length"
                                                    class="table-cell font-medium" v-html="formatDate(group.timestamp)">
                                                </td>
                                                <td v-if="recordIndex === 0" :rowspan="group.records.length"
                                                    class="table-cell">{{ group.name }}</td>
                                                <td v-if="recordIndex === 0" :rowspan="group.records.length"
                                                    class="table-cell">{{ group.user }}</td>
                                                <td v-if="recordIndex === 0" :rowspan="group.records.length"
                                                    class="table-cell">{{ group.error }}</td>
                                                <td class="table-cell">{{ record.index }}</td>
                                                <td class="table-cell font-medium" :class="getUsageColor(record.sm)">{{
                                                    record.sm }}%</td>
                                                <td class="table-cell font-medium" :class="getUsageColor(record.mem)">{{
                                                    record.mem }}%</td>
                                                <td class="table-cell">{{ convertToGB(record.mem_usage).replace(/ /g,
                                                    '&nbsp;') }} GB / {{ convertToGB(record.total_mem).replace('.00',
                                                        '') }} GB</td>
                                                <td class="table-cell">{{ record.command }}</td>
                                            </tr>
                                        </template>
                                    </tbody>
                                </table>
                            </div>
                            <!-- 分页控件 -->
                            <div class="mt-6 flex justify-between items-center">
                                <button @click="prevGpuPage" :disabled="gpuCurrentPage === 1" class="btn">上一页</button>
                                <span class="text-gray-600">
                                    第 <input v-model.number="gpuCurrentPage" @change="goToGpuPage" type="number"
                                        class="w-16 px-2 py-1 border rounded text-center"> 页，共 {{ gpuTotalPages }} 页
                                </span>
                                <span class="text-gray-600">
                                    每页条数：
                                    <input v-model.number="gpuItemsPerPage"
                                        @input="gpuItemsPerPage = validateItemsPerPage($event.target.value)"
                                        type="number" min="1" class="w-20 px-2 py-1 border rounded text-center"
                                        placeholder="每页条数">
                                </span>
                                <button @click="nextGpuPage" :disabled="gpuCurrentPage === gpuTotalPages"
                                    class="btn">下一页</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';
import { ENDPOINT } from '../config';
import UsageBar from './UsageBar.vue';
import InfoBox from './InfoBox.vue';

export default {
    components: {
        UsageBar,
        InfoBox,
    },
    setup() {
        const servers = ref([]);
        const cpuHistory = ref([]);
        const gpuHistory = ref([]);
        const isLoading = ref(true);

        // CPU 历史记录相关状态
        const cpuCurrentPage = ref(1);
        const cpuItemsPerPage = ref(10);
        const cpuSortKey = ref('timestamp');
        const cpuSortOrder = ref('desc');
        const cpuFilters = ref({ startDate: '', endDate: '', server: '', user: '' });

        // GPU 历史记录相关状态
        const gpuCurrentPage = ref(1);
        const gpuItemsPerPage = ref(10);
        const gpuSortKey = ref('timestamp');
        const gpuSortOrder = ref('desc');
        const gpuFilters = ref({ startDate: '', endDate: '', server: '', user: '', error: '' });

        // 监听 cpuItemsPerPage 的变化
        watch(cpuItemsPerPage, () => {
            cpuCurrentPage.value = 1;
        });

        // 监听 gpuItemsPerPage 的变化
        watch(gpuItemsPerPage, () => {
            gpuCurrentPage.value = 1;
        });

        // 添加验证函数
        const validateItemsPerPage = (value) => {
            const num = parseInt(value);
            return num >= 1 ? num : 10;
        };

        // 获取数据的函数
        const fetchStatus = async () => {
            try {
                isLoading.value = true;
                const response = await fetch(`${ENDPOINT}/api/status`);
                servers.value = await response.json();
            } catch (error) {
                console.error('获取服务器状态失败:', error);
            } finally {
                isLoading.value = false;
            }
        };

        const fetchCpuHistory = async () => {
            try {
                const response = await fetch(`${ENDPOINT}/api/cpu_history`);
                cpuHistory.value = await response.json();
            } catch (error) {
                console.error('获取 CPU 历史记录失败:', error);
            }
        };

        const fetchGpuHistory = async () => {
            try {
                const response = await fetch(`${ENDPOINT}/api/gpu_history`);
                gpuHistory.value = await response.json();
            } catch (error) {
                console.error('获取 GPU 历史记录失败:', error);
            }
        };

        // 修改 formatDate 函数
        const formatDate = (dateString) => {
            const date = new Date(dateString);
            const datePart = date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
            const timePart = date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            return `${datePart}<br>${timePart}`;
        };

        // 排序函数
        const sortCpuHistory = (key) => {
            if (cpuSortKey.value === key) {
                cpuSortOrder.value = cpuSortOrder.value === 'asc' ? 'desc' : 'asc';
            } else {
                cpuSortKey.value = key;
                cpuSortOrder.value = 'asc';
            }
        };

        // 筛选数
        const filterCpuHistory = () => {
            cpuCurrentPage.value = 1;
        };

        const filteredAndSortedCpuHistory = computed(() => {
            let result = cpuHistory.value.filter(record => {
                const recordDate = new Date(record.timestamp);
                const startDate = cpuFilters.value.startDate ? new Date(cpuFilters.value.startDate) : null;
                const endDate = cpuFilters.value.endDate ? new Date(cpuFilters.value.endDate) : null;

                return (
                    (!startDate || recordDate >= startDate) &&
                    (!endDate || recordDate <= endDate) &&
                    record.name.toLowerCase().includes(cpuFilters.value.server.toLowerCase()) &&
                    record.user.toLowerCase().includes(cpuFilters.value.user.toLowerCase()) &&
                    record.usage > 90
                );
            });

            result.sort((a, b) => {
                let modifier = cpuSortOrder.value === 'asc' ? 1 : -1;
                if (a[cpuSortKey.value] < b[cpuSortKey.value]) return -1 * modifier;
                if (a[cpuSortKey.value] > b[cpuSortKey.value]) return 1 * modifier;
                return 0;
            });

            return result;
        });

        const groupedCpuHistory = computed(() => {
            const grouped = [];
            let currentGroup = null;

            filteredAndSortedCpuHistory.value.forEach((record) => {
                if (!currentGroup ||
                    currentGroup.timestamp !== record.timestamp ||
                    currentGroup.name !== record.name ||
                    currentGroup.user !== record.user) {
                    if (currentGroup) {
                        grouped.push(currentGroup);
                    }
                    currentGroup = {
                        timestamp: record.timestamp,
                        name: record.name,
                        user: record.user,
                        records: []
                    };
                }
                currentGroup.records.push(record);
            });

            if (currentGroup) {
                grouped.push(currentGroup);
            }

            if (!isCpuDeduplicating.value) {
                return grouped;
            }

            // 去重逻辑
            const uniqueGrouped = [];
            const isCpuGroupEqual = (group1, group2) => {
                if (group1.name !== group2.name || group1.user !== group2.user || group1.records.length !== group2.records.length) {
                    return false;
                }
                const commandSets1 = group1.records.map(record => new Set(record.command));
                const commandSets2 = group2.records.map(record => new Set(record.command));

                for (let i = 0; i < commandSets1.length; i++) {
                    if (commandSets1[i].size !== commandSets2[i].size) {
                        return false;
                    }
                    for (const cmd of commandSets1[i]) {
                        if (!commandSets2[i].has(cmd)) {
                            return false;
                        }
                    }
                }
                return true;
            };

            for (const group of grouped) {
                if (!uniqueGrouped.some(uniqueGroup => isCpuGroupEqual(uniqueGroup, group))) {
                    uniqueGrouped.push(group);
                }
            }

            return uniqueGrouped;
        });

        // 修改 paginatedCpuHistory 计算属性
        const paginatedCpuHistory = computed(() => {
            const start = (cpuCurrentPage.value - 1) * cpuItemsPerPage.value;
            const end = start + cpuItemsPerPage.value;
            return groupedCpuHistory.value.slice(start, end);
        });

        // 修改 cpuTotalPages 计算属性
        const cpuTotalPages = computed(() => {
            return Math.ceil(groupedCpuHistory.value.length / cpuItemsPerPage.value);
        });

        // 页面导航函数
        const prevCpuPage = () => {
            if (cpuCurrentPage.value > 1) cpuCurrentPage.value--;
        };

        const nextCpuPage = () => {
            if (cpuCurrentPage.value < cpuTotalPages.value) cpuCurrentPage.value++;
        };

        const goToCpuPage = () => {
            const page = parseInt(cpuCurrentPage.value);
            if (page >= 1 && page <= cpuTotalPages.value) {
                cpuCurrentPage.value = page;
            } else {
                cpuCurrentPage.value = 1;
            }
        };

        // GPU 排序函数
        const sortGpuHistory = (key) => {
            if (gpuSortKey.value === key) {
                gpuSortOrder.value = gpuSortOrder.value === 'asc' ? 'desc' : 'asc';
            } else {
                gpuSortKey.value = key;
                gpuSortOrder.value = 'asc';
            }
        };

        // GPU 筛选函数
        const filterGpuHistory = () => {
            gpuCurrentPage.value = 1;
        };

        // 计算属性：过滤和排序后的 GPU 历史记录
        const filteredAndSortedGpuHistory = computed(() => {
            let result = gpuHistory.value.filter(record => {
                const recordDate = new Date(record.timestamp);
                const startDate = gpuFilters.value.startDate ? new Date(gpuFilters.value.startDate) : null;
                const endDate = gpuFilters.value.endDate ? new Date(gpuFilters.value.endDate) : null;

                return (
                    (!startDate || recordDate >= startDate) &&
                    (!endDate || recordDate <= endDate) &&
                    record.name.toLowerCase().includes(gpuFilters.value.server.toLowerCase()) &&
                    record.user.toLowerCase().includes(gpuFilters.value.user.toLowerCase()) &&
                    (record.error == null || record.error.toString().toLowerCase().includes(gpuFilters.value.error.toLowerCase()))
                );
            });

            result.sort((a, b) => {
                let modifier = gpuSortOrder.value === 'asc' ? 1 : -1;
                if (gpuSortKey.value === 'error') {
                    const aError = a.error == null ? '' : a.error.toString();
                    const bError = b.error == null ? '' : b.error.toString();
                    return aError.localeCompare(bError) * modifier;
                }
                if (a[gpuSortKey.value] < b[gpuSortKey.value]) return -1 * modifier;
                if (a[gpuSortKey.value] > b[gpuSortKey.value]) return 1 * modifier;
                return 0;
            });

            return result;
        });

        const isCpuDeduplicating = ref(false);
        const isGpuDeduplicating = ref(false);

        const toggleCpuDeduplication = () => {
            isCpuDeduplicating.value = !isCpuDeduplicating.value;
        };

        const toggleGpuDeduplication = () => {
            isGpuDeduplicating.value = !isGpuDeduplicating.value;
        };

        const groupedGpuHistory = computed(() => {
            const grouped = [];
            let currentGroup = null;

            filteredAndSortedGpuHistory.value.forEach((record) => {
                if (!currentGroup ||
                    currentGroup.timestamp !== record.timestamp ||
                    currentGroup.name !== record.name ||
                    currentGroup.user !== record.user ||
                    currentGroup.error !== record.error) {
                    if (currentGroup) {
                        grouped.push(currentGroup);
                    }
                    currentGroup = {
                        timestamp: record.timestamp,
                        name: record.name,
                        user: record.user,
                        error: record.error,
                        records: []
                    };
                }
                currentGroup.records.push(record);
            });

            if (currentGroup) {
                grouped.push(currentGroup);
            }

            if (!isGpuDeduplicating.value) {
                return grouped;
            }

            // 去重逻辑
            const uniqueGrouped = [];
            const isGpuGroupEqual = (group1, group2) => {
                if (group1.name !== group2.name || group1.error !== group2.error || group1.user !== group2.user || group1.records.length !== group2.records.length) {
                    return false;
                }

                const commandSets1 = group1.records.map(record => new Set(record.command.split(';')));
                const commandSets2 = group2.records.map(record => new Set(record.command.split(';')));

                for (let i = 0; i < commandSets1.length; i++) {
                    if (commandSets1[i].size !== commandSets2[i].size) {
                        return false;
                    }
                    for (const cmd of commandSets1[i]) {
                        if (!commandSets2[i].has(cmd)) {
                            return false;
                        }
                    }
                }
                return true;
            };

            for (const group of grouped) {
                if (!uniqueGrouped.some(uniqueGroup => isGpuGroupEqual(uniqueGroup, group))) {
                    uniqueGrouped.push(group);
                }
            }

            return uniqueGrouped;
        });

        // 修改 paginatedGpuHistory 计算属性
        const paginatedGpuHistory = computed(() => {
            const start = (gpuCurrentPage.value - 1) * gpuItemsPerPage.value;
            const end = start + gpuItemsPerPage.value;
            return groupedGpuHistory.value.slice(start, end);
        });

        // 修改 gpuTotalPages 计算属性
        const gpuTotalPages = computed(() => {
            return Math.ceil(groupedGpuHistory.value.length / gpuItemsPerPage.value);
        });

        // GPU 页面导航函数
        const prevGpuPage = () => {
            if (gpuCurrentPage.value > 1) gpuCurrentPage.value--;
        };

        const nextGpuPage = () => {
            if (gpuCurrentPage.value < gpuTotalPages.value) gpuCurrentPage.value++;
        };

        const goToGpuPage = () => {
            const page = parseInt(gpuCurrentPage.value);
            if (page >= 1 && page <= gpuTotalPages.value) {
                gpuCurrentPage.value = page;
            } else {
                gpuCurrentPage.value = 1;
            }
        };

        // 在 setup 函数中添加以下方法：
        const getUsageColor = (usage) => {
            if (usage < 50) return 'text-green-500';
            if (usage < 80) return 'text-yellow-500';
            return 'text-red-500';
        };

        // 添加 MB 到 GB 的转换函数
        const convertToGB = (mb) => {
            const gb = (mb / 1024).toFixed(2);
            return gb.padStart(5, ' ');
        };

        onMounted(() => {
            fetchStatus();
            fetchCpuHistory();
            fetchGpuHistory();
            setInterval(fetchStatus, 10 * 60 * 1000);
        });

        return {
            servers,
            isLoading,
            formatDate,
            // CPU 历史记录相关
            paginatedCpuHistory,
            cpuCurrentPage,
            cpuTotalPages,
            cpuSortKey,
            cpuSortOrder,
            cpuFilters,
            sortCpuHistory,
            filterCpuHistory,
            prevCpuPage,
            nextCpuPage,
            goToCpuPage,
            // GPU 历史记录相关
            paginatedGpuHistory,
            gpuCurrentPage,
            gpuTotalPages,
            gpuSortKey,
            gpuSortOrder,
            gpuFilters,
            sortGpuHistory,
            filterGpuHistory,
            prevGpuPage,
            nextGpuPage,
            goToGpuPage,
            groupedGpuHistory: paginatedGpuHistory,
            groupedCpuHistory: paginatedCpuHistory,
            getUsageColor,
            convertToGB,
            cpuItemsPerPage,
            gpuItemsPerPage,
            validateItemsPerPage,
            isCpuDeduplicating,
            isGpuDeduplicating,
            toggleCpuDeduplication,
            toggleGpuDeduplication,
        };
    },
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=Source+Code+Pro:wght@400;500;700&display=swap');

body {
    font-family: 'Noto Sans SC', sans-serif;
}

h1,
h2,
h3,
h4,
h5,
h6 {
    font-family: 'Noto Sans SC', sans-serif;
}

.table-header {
    @apply py-3 px-4 border-b text-left text-sm font-semibold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors duration-200;
    font-family: 'Source Code Pro', monospace;
}

.table-cell {
    @apply px-4 py-3 whitespace-nowrap text-sm text-gray-600;
    font-family: 'Source Code Pro', monospace;
}

.btn {
    @apply px-4 py-2 bg-blue-500 text-white rounded-lg font-medium disabled:opacity-50 hover:bg-blue-600 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50;
}

.input {
    @apply px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm;
}

table {
    @apply w-full border-collapse bg-white shadow-md rounded-lg overflow-hidden;
}

thead {
    @apply bg-gray-50;
}

/* tbody tr:nth-child(even) {
    @apply bg-gray-50;
} */

tbody tr:hover {
    @apply bg-blue-50;
}

.bg-yellow-50 {
    background-color: #fefce8;
}

.bg-red-50 {
    background-color: #fef2f2;
}

/* 新增样式，用于时间戳单元格 */
.table-cell.font-medium {
    white-space: normal;
    line-height: 1.2;
}

.btn.bg-green-500 {
    @apply hover:bg-green-600;
}
</style>