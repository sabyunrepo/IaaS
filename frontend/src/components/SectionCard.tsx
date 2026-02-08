interface SectionCardProps {
  title: string
  description?: string
  required?: boolean
  children: React.ReactNode
}

export function SectionCard({ title, description, required, children }: SectionCardProps) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          {title}
          {required && <span className="ml-1 text-red-500">*</span>}
        </h2>
        {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
      </div>
      {children}
    </div>
  )
}
