<script lang="ts" setup>
const appName = import.meta.env.VITE_APP_NAME ? import.meta.env.VITE_APP_NAME : "Slurp"
const appIcon = import.meta.env.VITE_APP_ICON ? import.meta.env.VITE_APP_ICON : "simple-icons:cbs"
</script>
<template>
  <div class="flex flex-nowrap items-center">
    <UIcon :name="appIcon"/>
    <span class="pl-2 font-bold">{{ appName }}</span>
  </div>
</template>
