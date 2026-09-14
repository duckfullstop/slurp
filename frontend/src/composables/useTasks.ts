import {useQuery} from '@tanstack/vue-query'
import {computed, type MaybeRefOrGetter, toValue} from 'vue'
import {fetchTask, fetchTaskEvents, fetchTasks} from '../api/tasks'

export function useTasksQuery() {
  return useQuery({
    queryKey: ['tasks'],
    queryFn: fetchTasks
  })
}

export function useTaskQuery(taskId: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: ['task', taskId],
    queryFn: () => fetchTask(toValue(taskId)),
    enabled: computed(() => !!toValue(taskId))
  })
}

export function useTaskEventsQuery(taskId: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: ['taskEvents', taskId],
    queryFn: () => fetchTaskEvents(toValue(taskId)),
    enabled: computed(() => !!toValue(taskId))
  })
}


