import {useMutation, useQuery, useQueryClient} from '@tanstack/vue-query'
import {computed, type MaybeRefOrGetter, toValue} from 'vue'
import {abortTask, createTask, fetchTask, fetchTaskEvents, fetchTasks, retryTask} from '../api/tasks'

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

export function useCreateTaskMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["tasks"],
    mutationFn: createTask,
    onSuccess: () => {
      queryClient.invalidateQueries({queryKey: ['tasks']})
    }
  })
}

export function useAbortTaskMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: abortTask,
    onSuccess: (task) => {
      queryClient.setQueryData(['task', task.id], task)
      queryClient.invalidateQueries({queryKey: ['tasks']})
      queryClient.invalidateQueries({queryKey: ['taskEvents', task.id]})
    }
  })
}

export function useRetryTaskMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: retryTask,
    onSuccess: (task) => {
      queryClient.setQueryData(['task', task.id], task)
      queryClient.invalidateQueries({queryKey: ['tasks']})
      queryClient.invalidateQueries({queryKey: ['taskEvents', task.id]})
    }
  })
}
