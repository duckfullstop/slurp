<script lang="ts" setup>
const appName = import.meta.env.VITE_APP_NAME ? import.meta.env.VITE_APP_NAME : "Slurp"
</script>
<template>
  <div class="flex flex-nowrap items-center">
    <UIcon class="flex-1 text-2xl" name="simple-icons:cbs"/>
    <span class="flex-1 pl-2 font-bold text-2xl">{{ appName }}</span>
  </div>
</template>
