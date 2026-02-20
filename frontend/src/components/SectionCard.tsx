interface SectionCardProps {
  title: string
  description?: string
  required?: boolean
  children: React.ReactNode
}

export function SectionCard({ title, description, required, children }: SectionCardProps) {
  return (
    <div className="rounded-xl border border-[--color-border-default] bg-[--color-bg-surface] p-6 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-[--color-text-primary]">
          {title}
          {required && <span className="ml-1 text-red-500">*</span>}
        </h2>
        {description && <p className="mt-1 text-sm text-[--color-text-tertiary]">{description}</p>}
      </div>
      {children}
    </div>
  )
}
