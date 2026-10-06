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
  force: z.boolean().optional(),
})

export type CreateTaskInput = z.infer<typeof createTaskSchema>

export function parseUrlList(raw: string | undefined): string[] {
  return (raw ?? '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
}

export const createTaskBatchSchema = createTaskSchema.omit({url: true}).extend({
  urls: z.string({error: 'Enter at least one URL'}).superRefine((raw, ctx) => {
    const urls = parseUrlList(raw)
    if (urls.length === 0) {
      ctx.addIssue({code: 'custom', message: 'Enter at least one URL'})
      return
    }
    const invalid = urls.filter((u) => !z.url().safeParse(u).success)
    if (invalid.length > 0) {
      ctx.addIssue({code: 'custom', message: `The following are not valid URLs: ${invalid.join(', ')}`})
    }
  }),
})

export type CreateTaskBatchInput = z.infer<typeof createTaskBatchSchema>
