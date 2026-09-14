import {z} from 'zod'

export const FORMAT_OPTIONS: { value: string; label: string }[] = [
  {value: 'VIDEO_AUDIO', label: 'Video+Audio'},
  {value: 'VIDEO_ONLY', label: 'Video Only (muted)'},
  {value: 'AUDIO_ONLY', label: 'Audio Only'},
]

export const createTaskSchema = z.object({
  url: z.url('Enter a valid URL to a piece of web media'),
  slug: z.string({
    error: (issue) => issue.input === undefined ? "Please enter a slug" : "Not a string"
  }).min(1, 'Please enter a slug'),
  format: z.enum(['VIDEO_AUDIO', 'VIDEO_ONLY', 'AUDIO_ONLY']),
  target: z.string().min(1, 'Choose a target directory'),
})

export type CreateTaskInput = z.infer<typeof createTaskSchema>
