export interface FileUpload {
  file: File | null
  path: string | null
  uploading: boolean
  error: string | null
}

interface FileUploadFieldProps {
  label: string
  accept: string
  fileState: FileUpload
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  onRemove: () => void
  t: (key: string) => string
}

export function FileUploadField({
  label,
  accept,
  fileState,
  onFileChange,
  onRemove,
  t,
}: FileUploadFieldProps) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-[--color-text-secondary]">{label}</label>
      {fileState.path ? (
        <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100">
            <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span className="flex-1 truncate text-sm font-medium text-green-700">{fileState.file?.name}</span>
          <button
            type="button"
            onClick={onRemove}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-500"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      ) : (
        <label className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-[--color-border-default] bg-[--color-bg-page] p-4 transition-colors hover:border-[--color-border-accent] hover:bg-[--color-bg-surface-hover]">
          <svg className="mb-2 h-8 w-8 text-[--color-text-tertiary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <span className="text-sm text-[--color-text-secondary]">{accept} {t('file_select')}</span>
          <input
            type="file"
            accept={accept}
            onChange={onFileChange}
            disabled={fileState.uploading}
            className="hidden"
          />
        </label>
      )}
      {fileState.uploading && (
        <div className="mt-2 flex items-center gap-2 text-sm text-[--color-text-accent-strong]">
          <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {t('uploading')}
        </div>
      )}
      {fileState.error && <p className="mt-2 text-sm text-red-600">{fileState.error}</p>}
    </div>
  )
}
