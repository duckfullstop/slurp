<script lang="ts" setup>
import {computed} from "vue";
import {AccordionItem} from "@nuxt/ui";
import {useConfigQuery} from "../composables/useConfig.ts";

const {data: config, isLoading: isLoadingConfig, error: configError} = useConfigQuery()

const configFetcherList = computed<AccordionItem[]>(() => {
  const accordionItems: AccordionItem[] = []
  if (config.value?.fetchers) {
    for (const [key, item] of Object.entries(config.value.fetchers)) {
      accordionItems.push({
        label: key,
        services: item.services,
      })
    }
  }
  return accordionItems
})
</script>

<template>
  <UPageHero class="mt-0">
    <template #title>
      <AppLogo class="justify-center text-7xl" />
    </template>
    <template #description>
      A web media ingestion utility for the broadcast domain.
    </template>
  </UPageHero>
  <USeparator class="pb-10" />
  <UContainer>
    <UHeader
      class="pb-5"
      title="Available Fetchers"
    />
    <UCard class="w-full sm:w-200 justify-self-center">
      <p v-if="isLoadingConfig" />
      <p v-else-if="configError">
        <UAlert
          :description="configError.message"
          color="error"
          icon="pepicons-pop:exclamation-circle-filled"
          title="Error loading Config"
          variant="solid"
        />
      </p>
      <UAccordion
        v-else
        :items="configFetcherList"
        type="multiple"
      >
        <template #body="{ item }">
          <p class="text-lg pb-1">
            This fetcher can handle:
          </p>
          <ul class="list-disc list-inside">
            <li
              v-for="service in item.services"
              :key="service"
            >
              {{ service }}
            </li>
          </ul>
        </template>
      </UAccordion>
    </UCard>
  </UContainer>
</template>
