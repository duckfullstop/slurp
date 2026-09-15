<script lang="ts" setup>
const appName = import.meta.env.VITE_APP_NAME ? import.meta.env.VITE_APP_NAME : "Slurp"
const appIcon = import.meta.env.VITE_APP_ICON ? import.meta.env.VITE_APP_ICON : "simple-icons:cbs"
</script>
<template>
  <div class="flex flex-nowrap items-center">
    <UIcon :name="appIcon" class="flex-1 text-2xl"/>
    <span class="flex-1 pl-2 font-bold text-2xl">{{ appName }}</span>
  </div>
</template>
